import concurrent.futures
import datetime
import math
import os
import time
from pathlib import PurePath
from typing import Dict, Optional

import bugsnag
import humanize
import requests
import typer
from rich import print
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from tenacity import retry, stop_after_attempt, wait_fixed
from tqdm import tqdm

from cerebrium.api import cerebrium_request
from cerebrium.context import get_current_project, get_default_region
from cerebrium.utils.files import ProgressTracker
from cerebrium.utils.logging import cerebrium_log

CEREBRIUM_ENV = os.getenv("CEREBRIUM_ENV", "prod")

files_cli = typer.Typer(no_args_is_help=True)


@files_cli.command("ls")
def ls_files(
    path: Optional[str] = typer.Argument("/", help="Remote path to list contents"),
    region: Optional[str] = typer.Option(
        None, "--region", "-r", help="Region for the storage volume"
    ),
):
    """
        List contents of persistent storage. Run `cerebrium ls --help` for more information.\n
    \n
        Usage: cerebrium ls [OPTIONS] [REMOTE_PATH]\n
    \n
          List contents of persistent storage.\n
    \n
        Options:\n
          -h, --help          Show this message and exit.\n
    \n
        Examples:\n
          # List all files in the root directory\n
          cerebrium ls\n
    \n
          # List all files in a specific directory\n
          cerebrium ls sub_folder/\n
    """
    project_id = get_current_project()
    if not project_id:
        cerebrium_log(
            level="ERROR",
            message="No project configured. Please run 'cerebrium login' to authenticate.",
            prefix="",
        )
        raise typer.Exit(1)

    # Use provided region or fall back to default
    actual_region = region if region else get_default_region()

    data = _remote_ls(path, actual_region, project_id)

    table = Table(show_header=True, header_style="bold yellow")

    table.add_column("Name", style="dim")
    table.add_column("Size", style="dim", width=15)
    table.add_column("Last Modified", width=20)

    if not data or len(data) == 0:
        print("[yellow]No files found.[/yellow]")
        raise typer.Exit(0)

    for item in data:
        name = item["name"]
        size = (
            humanize.naturalsize(item.get("size_bytes", 0))
            if not item["is_folder"]
            else "Directory"
        )
        last_modified = item["last_modified"]
        if last_modified == "0001-01-01T00:00:00Z":
            last_modified = "N/A"
        else:
            last_modified = datetime.datetime.fromisoformat(
                last_modified.replace("Z", "+00:00")
            ).strftime("%Y-%m-%d %H:%M:%S")

        table.add_row(name, size, last_modified)

    print(table)


def upload_single_file(
    src, dest, project_id, region, part_size_mb=50, pbar=None, progress_tracker=None
):
    file_size = os.path.getsize(src)
    part_size = part_size_mb * 1024 * 1024
    part_count = math.ceil(file_size / part_size)

    response = cerebrium_request(
        "POST",
        f"v2/projects/{project_id}/volumes/default/cp/initialize?region={region}",
        {"file_path": dest, "part_count": part_count, "region": region},
        requires_auth=True,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        cerebrium_log(
            level="ERROR",
            message=f"Failed to initiate file copy: {response.text}",
            prefix="",
        )
        bugsnag.notify(e, severity="error")
        raise typer.Exit(1)

    data = response.json()
    upload_id = data["upload_id"]
    parts = data["parts"]

    # Set total parts for progress tracking (only if not disabled for directory operations)
    if progress_tracker and progress_tracker.total_parts == 0:
        # Only set parts if it hasn't been explicitly disabled
        if not hasattr(progress_tracker, "_parts_disabled"):
            progress_tracker.set_total_parts(len(parts))

    # Don't use tqdm.write here to avoid duplicate progress bars
    if progress_tracker:
        progress_tracker.set_current_filename(os.path.basename(src))

    if part_count == 0 and file_size == 0:
        return typer.Exit(0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(8),
        retry=lambda e: isinstance(e, requests.HTTPError),
        retry_error_callback=lambda e: typer.Exit(1),
    )
    def upload_part(part) -> Dict[str, str]:
        part_number = part["part_number"]
        url = part["url"]

        # Mark part as started
        if progress_tracker:
            progress_tracker.part_started()

        try:
            with open(src, "rb") as file:
                file.seek((part_number - 1) * part_size)
                part_data = file.read(part_size)

            # Use streaming upload for better progress tracking
            put_response = requests.put(url, data=part_data, stream=False)
            uploaded_size = len(part_data)

            # Simulate streaming progress for fluid updates
            chunk_size = 1024 * 1024  # 1MB chunks for progress simulation
            if uploaded_size > chunk_size:
                for i in range(0, uploaded_size, chunk_size):
                    chunk = min(chunk_size, uploaded_size - i)
                    if progress_tracker:
                        progress_tracker.update(chunk)
                        time.sleep(0.02)  # 20ms for very smooth progress
            else:
                # For small parts, update immediately
                if progress_tracker:
                    progress_tracker.update(uploaded_size)

            try:
                put_response.raise_for_status()
            except requests.HTTPError as e:
                tqdm.write(f"Failed to upload part {part_number}: {e}, retrying...")
                raise e

            # Progress already updated in the streaming loop above

            return {"part_number": part_number, "etag": put_response.headers["ETag"]}
        finally:
            # Mark part as completed
            if progress_tracker:
                progress_tracker.part_completed()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        uploaded_parts = list(executor.map(upload_part, parts))

    response = cerebrium_request(
        "POST",
        f"v2/projects/{project_id}/volumes/default/cp/complete?region={region}",
        {
            "upload_id": upload_id,
            "file_path": dest,
            "parts": uploaded_parts,
            "region": region,
        },
        requires_auth=True,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        cerebrium_log(
            level="ERROR",
            message=f"Failed to complete file copy: {response.text}",
            prefix="",
        )
        bugsnag.notify(e, severity="error")
        raise typer.Exit(1)

    # File upload completed - progress tracker will show status


def _remote_ls(path: Optional[str], region: str, project_id: Optional[str]):
    response = cerebrium_request(
        "GET",
        f"v2/projects/{project_id}/volumes/default/ls?region={region}",
        {"dir": path},
        requires_auth=True,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        try:
            error_json = response.json()
            error_message = error_json.get("message")
        except Exception:
            error_message = None

        display_message = (
            f"There was an error listing your files: {error_message}. Please try again and if the problem persists contact support."
            if error_message
            else f"There was an error listing your files: {response.text}. Please try again and if the problem persists contact support."
        )

        cerebrium_log(
            level="ERROR",
            message=display_message,
            prefix="",
        )
        bugsnag.notify(e, severity="error")
        raise typer.Exit(1)

    data = response.json()
    return data


def _remote_path_type(path: Optional[str], region: str, project_id: Optional[str]):
    if not path:
        return "not_found"

    pure_path = PurePath(path)
    parent_path = pure_path.parent.as_posix()
    filename = pure_path.parts[-1]

    # A heuristic to decide whether the destination is a folder or file.
    # We fallback on this if the destination does not exist.
    file_type_heuristic = "folder" if path[-1] == "/" else "file"

    ls_data = _remote_ls(parent_path, region, project_id)
    if not ls_data:
        return file_type_heuristic
    # Find the given path in the list of file data given.
    chosen_file_data = [file for file in ls_data if file["name"] in (filename, filename + "/")]
    # `dest` does not exist in a folder so this file or directory doesn't yet exist. Fall back to heuristic.
    if len(chosen_file_data) == 0:
        return file_type_heuristic

    return "folder" if chosen_file_data[0]["is_folder"] else "file"


@files_cli.command("cp")
def cp_file(
    src: str = typer.Argument(..., help="Path to the source file or directory to be uploaded."),
    dest: str = typer.Argument(
        None,
        help="Destination path on the server where the file(s) should be uploaded.",
    ),
    region: Optional[str] = typer.Option(
        None, "--region", "-r", help="Region for the storage volume"
    ),
):
    """
        Copy contents to persistent storage. Run `cerebrium cp --help` for more information.\n
    \n
        Usage: cerebrium cp [OPTIONS] LOCAL_PATH REMOTE_PATH (Optional)\n
    \n
          Copy contents to persistent storage.\n
    \n
        Options:\n
          -h, --help          Show this message and exit.\n
    \n
        Examples:\n
          # Copy a single file\n
          cerebrium cp src_file_name.txt # copies to /src_file_name.txt\n
          cerebrium cp src_file_name.txt dest_file_name.txt # copies to /dest_file_name.txt\n
    \n
          # Copy a directory\n
          cerebrium cp dir_name # copies to the root directory\n
          cerebrium cp dir_name sub_folder/ # copies to sub_folder/\n
    """
    project_id = get_current_project()
    if not project_id:
        cerebrium_log(
            level="ERROR",
            message="No project configured. Please run 'cerebrium login' to authenticate.",
            prefix="",
        )
        raise typer.Exit(1)

    # Use provided region or fall back to default
    actual_region = region if region else get_default_region()

    if dest is None:
        # Set the destination to the root directory or to a name based on the source
        if os.path.isdir(src):
            dest = "/"
        else:
            dest = f"/{os.path.basename(src)}"

    total_size = 0
    file_paths = []

    if os.path.isdir(src):
        for root, _, files in os.walk(src):
            for file_name in files:
                file_src = os.path.join(root, file_name)
                file_size = os.path.getsize(file_src)
                total_size += file_size
                file_dest = os.path.join(dest, os.path.relpath(file_src, src))
                file_paths.append((file_src, file_dest))
    else:
        file_size = os.path.getsize(src)
        dest_type = _remote_path_type(dest, actual_region, project_id)
        actual_file_dest = dest
        if dest_type == "folder":
            actual_file_dest = os.path.join(dest, os.path.basename(src))
        elif dest[-1] == "/" and dest_type == "file":
            print("[yellow]Destination path is a file not a directory[/yellow]")
            raise typer.Exit(1)

        total_size += file_size
        file_paths.append((src, actual_file_dest))

    # Create a spinner that shows upload status
    spinner = Spinner("dots", "Preparing upload...", style="gray")
    live = Live(spinner, refresh_per_second=10)
    live.start()

    try:
        # Create progress tracker with spinner
        progress_tracker = ProgressTracker(total_size, None, spinner, live, "Uploading")

        progress_tracker.disable_parts_tracking()

        # Start the background update thread
        progress_tracker.start_update_thread()

        try:
            for file_src, file_dest in file_paths:
                # Update current filename
                filename = os.path.basename(file_src)
                progress_tracker.set_current_filename(filename)

                upload_single_file(
                    file_src,
                    file_dest,
                    project_id,
                    actual_region,
                    progress_tracker=progress_tracker,
                )
        finally:
            # Stop the background update thread before showing completion
            progress_tracker.stop_update_thread()
            # Small delay to ensure spinner stops
            time.sleep(0.3)

        # Show completion message
        total_size_str = human_readable_size(total_size)
        print(f"\n[green]✓ Upload completed successfully! Total: {total_size_str}[/green]")
    finally:
        live.stop()


def human_readable_size(size, decimal_places=2):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0
    return f"{size:.{decimal_places}f} PB"


def download_single_file(src, dest, project_id, region, progress_tracker=None):
    """
    Download a single file from persistent storage.

    Args:
        src (str): Remote path to the file to download
        dest (str): Local path where the file should be saved
        project_id (str): Project ID to use for the API request
        region (str): Region for the storage volume
        progress_tracker (ProgressTracker, optional): Progress tracker for download progress
    """
    response = cerebrium_request(
        "GET",
        f"v2/projects/{project_id}/volumes/default/download?region={region}",
        {"file_path": src, "region": region},
        requires_auth=True,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        cerebrium_log(
            level="ERROR",
            message=f"Failed to get download URL: {response.text}",
            prefix="",
        )
        bugsnag.notify(e, severity="error")
        raise typer.Exit(1)

    try:
        download_url = response.json().get("url")
        if not download_url:
            cerebrium_log(
                level="ERROR",
                message="Failed to get download URL from response",
                prefix="",
            )
            bugsnag.notify(Exception("No download URL in response"), severity="error")
            raise typer.Exit(1)
    except ValueError as e:
        cerebrium_log(
            level="ERROR",
            message=f"Failed to parse response: {e}",
            prefix="",
        )
        bugsnag.notify(e, severity="error")
        raise typer.Exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)

    download_response = requests.get(download_url, stream=True)
    try:
        download_response.raise_for_status()
    except requests.HTTPError as e:
        cerebrium_log(
            level="ERROR",
            message="Failed to download file.",
            prefix="",
        )
        bugsnag.notify(e, severity="error")
        raise typer.Exit(1)

    total_size = int(download_response.headers.get("content-length", 0))

    # Update current filename for progress tracking (if progress tracker provided)
    if progress_tracker:
        filename = os.path.basename(src)
        progress_tracker.set_current_filename(filename)

    with open(dest, "wb") as f:
        for chunk in download_response.iter_content(chunk_size=8192):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                if progress_tracker:
                    progress_tracker.update(len(chunk))

    return total_size


def collect_directory_files(
    path: str, region: str, project_id: str, base_path: str = "", max_depth: int = 100
) -> list[tuple[str, int]]:
    """
    Recursively collect all files in a directory from remote storage.

    Args:
        path (str): Remote directory path to collect files from
        region (str): Region for the storage volume
        project_id (str): Project ID to use for the API request
        base_path (str): Base path for tracking relative paths
        max_depth (int): Maximum recursion depth to prevent infinite loops

    Returns:
        list[tuple[str, int]]: List of (file_path, file_size) tuples
    """
    files = []

    # Prevent infinite recursion
    if max_depth <= 0:
        cerebrium_log(
            level="WARNING",
            message=f"Maximum recursion depth reached for directory: {path}",
            prefix="",
        )
        return files

    try:
        data = _remote_ls(path, region, project_id)
        if not data:
            return files

        for item in data:
            item_name = item["name"]
            item_path = f"{path.rstrip('/')}/{item_name}" if path != "/" else f"/{item_name}"

            if item["is_folder"]:
                subdir_files = collect_directory_files(
                    item_path, region, project_id, base_path, max_depth - 1
                )
                files.extend(subdir_files)
            else:
                file_size = item.get("size_bytes", 0)
                files.append((item_path, file_size))

    except Exception as e:
        cerebrium_log(
            level="ERROR",
            message=f"Failed to list directory contents for {path}: {e}",
            prefix="",
        )

    return files


@files_cli.command("download")
def download_file(
    src: str = typer.Argument(
        ..., help="Remote path to the file or directory to be downloaded."
    ),
    dest: str = typer.Argument(
        None, help="Local destination path where the file(s) should be saved."
    ),
    region: Optional[str] = typer.Option(
        None, "--region", "-r", help="Region for the storage volume"
    ),
):
    """
        Download a file or directory from persistent storage. Run `cerebrium download --help` for more information.\n
    \n
        Usage: cerebrium download [OPTIONS] REMOTE_PATH [LOCAL_PATH]\n
    \n
          Download a file or directory from persistent storage.\n
    \n
        Options:\n
          -h, --help          Show this message and exit.\n
    \n
        Examples:\n
          # Download a single file\n
          cerebrium download file_name.txt\n
          cerebrium download file_name.txt local_file_name.txt\n
          cerebrium download sub_folder/file_name.txt\n
    \n
          # Download a directory\n
          cerebrium download my_folder/\n
          cerebrium download my_folder/ ./local_folder/\n
    """
    project_id = get_current_project()
    if not project_id:
        cerebrium_log(
            level="ERROR",
            message="No project configured. Please run 'cerebrium login' to authenticate.",
            prefix="",
        )
        raise typer.Exit(1)

    actual_region = region if region else get_default_region()

    src_type = _remote_path_type(src, actual_region, project_id)

    if src_type == "folder":
        if dest is None:
            dest = os.path.basename(src.rstrip("/"))

        # Discovery phase with spinner for large directories
        discovery_spinner = Spinner("dots", "Discovering files...", style="gray")
        discovery_live = Live(discovery_spinner, refresh_per_second=10)
        discovery_live.start()

        try:
            file_list = collect_directory_files(src, actual_region, project_id)
        finally:
            discovery_live.stop()

        if not file_list:
            print("[yellow]No files found in the specified directory.[/yellow]")
            return

        total_size = sum(size for _, size in file_list)
        file_count = len(file_list)

        print(
            f"[cyan]Found {file_count} files to download ({human_readable_size(total_size)})[/cyan]"
        )

        spinner = Spinner("dots", "Preparing download...", style="gray")
        live = Live(spinner, refresh_per_second=10)
        live.start()

        try:
            progress_tracker = ProgressTracker(total_size, None, spinner, live, "Downloading")

            # Disable parts tracking for directory downloads (we're downloading multiple files, not parts)
            progress_tracker.disable_parts_tracking()

            progress_tracker.start_update_thread()

            try:
                downloaded_count = 0
                for remote_file_path, file_size in file_list:
                    rel_path = os.path.relpath(remote_file_path, src)
                    local_file_path = os.path.join(dest, rel_path)

                    os.makedirs(
                        os.path.dirname(os.path.abspath(local_file_path)), exist_ok=True
                    )

                    download_single_file(
                        remote_file_path,
                        local_file_path,
                        project_id,
                        actual_region,
                        progress_tracker,
                    )

                    downloaded_count += 1

                    if progress_tracker.spinner:
                        progress_tracker.spinner.text = (
                            f"Downloaded {downloaded_count}/{file_count} files..."
                        )

            finally:
                progress_tracker.stop_update_thread()
                time.sleep(0.3)

            total_size_str = human_readable_size(total_size)
            print(
                f"\n[green]✓ Download completed successfully! Downloaded {file_count} files ({total_size_str})[/green]"
            )

        finally:
            live.stop()

    else:
        # Handle single file download
        if dest is None:
            dest = os.path.basename(src)

        # Create progress tracker for single file download
        spinner = Spinner("dots", "Preparing download...", style="gray")
        live = Live(spinner, refresh_per_second=10)
        live.start()

        try:
            # Get the file size first, then create progress tracker with correct size
            # Get download URL to check file size
            response = cerebrium_request(
                "GET",
                f"v2/projects/{project_id}/volumes/default/download?region={actual_region}",
                {"file_path": src, "region": actual_region},
                requires_auth=True,
            )

            try:
                response.raise_for_status()
                download_url = response.json().get("url")
                if not download_url:
                    raise Exception("No download URL in response")
            except Exception as e:
                cerebrium_log(
                    level="ERROR", message=f"Failed to get download URL: {e}", prefix=""
                )
                raise typer.Exit(1)

            # Get file size from headers
            head_response = requests.head(download_url)
            file_size = int(head_response.headers.get("content-length", 0))

            # Create progress tracker with correct file size from the start
            progress_tracker = ProgressTracker(file_size, None, spinner, live, "Downloading")
            progress_tracker.start_update_thread()

            try:
                actual_file_size = download_single_file(
                    src, dest, project_id, actual_region, progress_tracker
                )

                # Show completion message
                file_size_str = (
                    human_readable_size(actual_file_size) if actual_file_size > 0 else "0 B"
                )
                print(f"\n[green]✓ Download completed successfully! ({file_size_str})[/green]")
            finally:
                progress_tracker.stop_update_thread()
                time.sleep(0.3)
        finally:
            live.stop()


@files_cli.command("rm")
def rm_file(
    remote_path: str = typer.Argument(..., help="Path to the file or directory to be removed."),
    region: Optional[str] = typer.Option(
        None, "--region", "-r", help="Region for the storage volume"
    ),
):
    """
        Remove a file or directory from persistent storage. Run `cerebrium rm --help` for more information.\n
    \n
        Usage: cerebrium rm [OPTIONS] REMOTE_PATH\n
    \n
          Remove a file or directory from persistent storage.\n
    \n
        Options:\n
          -h, --help          Show this message and exit.\n
    \n
        Examples:\n
          # Remove a specific file\n
          cerebrium rm /file_name.txt\n
          cerebrium rm /sub_folder/file_name.txt\n
    \n
          # Remove a directory and all its contents\n
          cerebrium rm /sub_folder/ # Note that it must end with a forward slash /\n
          cerebrium rm / # Removes all files in the root directory\n
    """
    project_id = get_current_project()
    if not project_id:
        cerebrium_log(
            level="ERROR",
            message="No project configured. Please run 'cerebrium login' to authenticate.",
            prefix="",
        )
        raise typer.Exit(1)

    # Use provided region or fall back to default
    actual_region = region if region else get_default_region()

    response = cerebrium_request(
        "DELETE",
        f"v2/projects/{project_id}/volumes/default/rm?region={actual_region}",
        {"file_path": remote_path, "region": actual_region},
        requires_auth=True,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        cerebrium_log(
            level="ERROR",
            message=f"Failed to remove file: {response.text}",
            prefix="",
        )
        bugsnag.notify(e, severity="error")
        raise typer.Exit(1)

    print(f"[green]{remote_path} removed successfully.[/green]")
