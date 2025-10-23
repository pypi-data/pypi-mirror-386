import fnmatch
import os
import re
import threading
import time
from pathlib import Path

from cerebrium.utils.logging import cerebrium_log


# Thread-safe progress tracking
class ProgressTracker:
    def __init__(
        self, total_size: int, pbar=None, spinner=None, live=None, action_text="Processing"
    ):
        self.total_size = total_size
        self.pbar = pbar
        self.spinner = spinner
        self.live = live
        self.uploaded_size = 0
        self.lock = threading.Lock()
        self.active_uploads = 0
        self.total_parts = 0
        self.completed_parts = 0
        self.current_filename = ""
        self.should_stop = False
        self.update_thread = None
        self.action_text = action_text

    def update(self, size: int):
        with self.lock:
            self.uploaded_size += size
            if self.pbar:
                self.pbar.update(size)

    def set_total_parts(self, parts: int):
        with self.lock:
            self.total_parts = parts

    def set_current_filename(self, filename: str):
        with self.lock:
            self.current_filename = filename

    def disable_parts_tracking(self):
        """Disable parts tracking for directory operations"""
        with self.lock:
            self.total_parts = 0
            self.completed_parts = 0
            self._parts_disabled = True

    def part_started(self):
        with self.lock:
            self.active_uploads += 1

    def part_completed(self):
        with self.lock:
            self.active_uploads -= 1
            if not getattr(self, "_parts_disabled", False):
                self.completed_parts += 1

    def get_status_text(self) -> str:
        with self.lock:
            if self.total_parts > 0:
                return f"{self.action_text} {self.current_filename}... ({self.completed_parts}/{self.total_parts} parts)"
            else:
                return f"{self.action_text} {self.current_filename}..."

    def get_progress_percentage(self) -> float:
        with self.lock:
            if self.total_size > 0:
                return (self.uploaded_size / self.total_size) * 100
            return 0.0

    def start_update_thread(self):
        """Start a background thread that updates the spinner with progress"""
        if self.spinner and self.live:
            self.should_stop = False
            self.update_thread = threading.Thread(target=self._update_spinner_loop, daemon=True)
            self.update_thread.start()

    def stop_update_thread(self):
        """Stop the background update thread"""
        self.should_stop = True
        if self.update_thread:
            self.update_thread.join(timeout=1)

    def _update_spinner_loop(self):
        """Background thread that updates the spinner with current progress"""
        while not self.should_stop:
            try:
                status_text = self.get_status_text()
                progress_bar = self._create_progress_bar()

                if self.spinner and self.live and not self.should_stop:
                    self.spinner.text = f"{status_text}\n{progress_bar}"

                time.sleep(0.1)  # Update every 100ms for fluid feel
            except Exception:
                # Ignore any errors in the update thread
                break

    def _create_progress_bar(self) -> str:
        """Create a slim, fluid progress bar"""
        if self.total_size == 0:
            return ""

        percentage = (self.uploaded_size / self.total_size) * 100
        bar_length = 40  # Slimmer bar
        filled_length = int(bar_length * percentage / 100)

        bar = "▰" * filled_length + "▱" * (bar_length - filled_length)

        uploaded_size_str = self._human_readable_size(self.uploaded_size)
        total_size_str = self._human_readable_size(self.total_size)

        return f"{bar} {percentage:.1f}% ({uploaded_size_str}/{total_size_str})"

    def _human_readable_size(self, size, decimal_places=1):
        """Convert bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024.0
        return f"{size:.{decimal_places}f} PB"


def ensure_pattern_format(pattern: str):
    if not pattern:
        return pattern
    sep = os.path.sep
    if pattern.startswith(f"{sep}"):  # Starts with /
        cerebrium_log(
            prefix="ValueError",
            level="ERROR",
            message="Pattern cannot start with a forward slash. Please use a relative path.",
        )
        raise ValueError(
            "Pattern cannot start with a forward slash. Please use a relative path."
        )
    if pattern.endswith(sep):
        pattern = os.path.join(pattern, "*")
    elif os.path.isdir(pattern) and not pattern.endswith(sep):
        pattern = os.path.join(pattern, "*")

    pattern = str(Path(pattern))
    return pattern


def determine_includes(include: list[str], exclude: list[str]):
    include_set = [i.strip() for i in include]
    include_set = set(map(ensure_pattern_format, include_set))

    exclude_set = [e.strip() for e in exclude]
    exclude_set = set(map(ensure_pattern_format, exclude_set))

    file_list: list[str] = []
    for root, _, files in os.walk("."):
        for file in files:
            full_path = str(Path(root) / file)
            if any(fnmatch.fnmatch(full_path, pattern) for pattern in include_set) and not any(
                fnmatch.fnmatch(full_path, pattern) for pattern in exclude_set
            ):
                file_list.append(full_path)
    return file_list


def detect_dev_folders(file_list: list[str]) -> list[str]:
    """
    Detects development folders in the root directory of the file list.

    Args:
        file_list (list[str]): List of files to check.

    Returns:
        list[str]: List of detected development folders.
    """
    venv_folder_names = ["venv", "virtualenv", ".venv", ".git"]
    venv_pattern = re.compile(r"^\.venv-\d+\.\d+")  # Matches .venv-3.12, .venv-3.11, etc.
    detected_folders = []

    for folder_name in venv_folder_names:
        if any(f.startswith(f"{folder_name}/") for f in file_list):
            detected_folders.append(folder_name)

    # Check for version-specific venv folders using regex patterns
    root_folders = set()
    for f in file_list:
        if "/" in f:
            root_folder = f.split("/")[0]
            root_folders.add(root_folder)

    for folder in root_folders:
        if venv_pattern.match(folder):
            detected_folders.append(folder)

    return detected_folders
