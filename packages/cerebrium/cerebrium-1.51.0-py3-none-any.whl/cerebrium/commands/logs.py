import time
import re
from datetime import datetime, timedelta
from typing import Annotated, Optional, List, Dict, Tuple, TypedDict
from urllib.parse import urlencode

import bugsnag
import typer
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from cerebrium.api import cerebrium_request
from cerebrium.context import get_current_project
from cerebrium.utils.logging import cerebrium_log, console

logs_cli = typer.Typer(no_args_is_help=True)


def parse_since_timestamp(since_str: str) -> str:
    """
    Parse a --since parameter and return an ISO timestamp string.

    Args:
        since_str: Either a relative time (e.g., "1h", "30m", "2d") or ISO datetime string

    Returns:
        ISO timestamp string

    Raises:
        typer.Exit: If the format is invalid
    """
    # Try to parse as ISO datetime first
    try:
        # Handle Z suffix by converting to +00:00 for parsing, then back to Z for output
        if since_str.endswith("Z"):
            dt = datetime.fromisoformat(since_str.replace("Z", "+00:00"))
            # Truncate to milliseconds to match ClickHouse precision (3 decimal places)
            dt = dt.replace(microsecond=dt.microsecond // 1000 * 1000)
            return dt.isoformat().replace("+00:00", "Z")
        else:
            dt = datetime.fromisoformat(since_str)
            # Truncate to milliseconds to match ClickHouse precision (3 decimal places)
            dt = dt.replace(microsecond=dt.microsecond // 1000 * 1000)
            return dt.isoformat()
    except ValueError:
        pass

    # Parse relative time format (e.g., "1h", "30m", "2d")
    relative_time_pattern = r"^(\d+)([smhd])$"
    match = re.match(relative_time_pattern, since_str)

    if not match:
        cerebrium_log(
            level="ERROR",
            message=f"Invalid --since format: '{since_str}'. Use relative time (e.g., '1h', '30m') or ISO datetime.",
            prefix="",
        )
        raise typer.Exit(1)

    amount, unit = match.groups()
    amount = int(amount)

    unit_map = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}

    if unit not in unit_map:
        cerebrium_log(
            level="ERROR",
            message=f"Invalid time unit: '{unit}'. Use s, m, h, or d.",
            prefix="",
        )
        raise typer.Exit(1)

    delta_kwargs = {unit_map[unit]: amount}
    target_time = datetime.utcnow() - timedelta(**delta_kwargs)

    return target_time.isoformat() + "Z"


class LogEntry(TypedDict):
    appId: str
    projectId: str
    runId: str
    containerId: str
    containerName: str
    logId: str
    lineNumber: int
    logLine: str
    stream: str  # "stdout" or "stderr"
    timestamp: str


class LogsResponse(TypedDict):
    logs: List[LogEntry]
    nextPageToken: Optional[str]
    hasMore: bool


@logs_cli.command(
    "logs",
    help="""
Usage: cerebrium logs APP_NAME [OPTIONS]

  Fetch and display logs for the specified app, following by default.

Options:
  --no-follow         Don't follow log output (fetch once and exit)
  --since TEXT        Show logs since timestamp (e.g., "1h", "30m", "2023-12-01T10:00:00")
  -h, --help          Show this message and exit.

Examples:
  # Follow logs continuously (default behavior)
  cerebrium logs app-name

  # Get logs once without following
  cerebrium logs app-name --no-follow

  # Get logs from the last hour
  cerebrium logs app-name --since "1h"

  # Get logs since a specific datetime
  cerebrium logs app-name --since "2023-12-01T10:00:00"
    """,
)
def watch_app_logs(
    app_name: Annotated[
        str,
        typer.Argument(
            ...,
            help="The app-name you would like to see the logs for",
        ),
    ],
    no_follow: Annotated[
        bool,
        typer.Option(
            "--no-follow",
            help="Don't follow log output (fetch once and exit)",
        ),
    ] = False,
    since: Annotated[
        Optional[str],
        typer.Option(
            "--since",
            help="Show logs since timestamp (e.g., '1h', '30m', '2023-12-01T10:00:00')",
        ),
    ] = None,
):
    """
    Fetch and display logs for the specified app, following by default unless --no-follow is specified.
    """
    project_id = get_current_project()

    if project_id is None:
        cerebrium_log(
            level="ERROR",
            message="You are not currently in a project. Please login and try again.",
            prefix="",
        )
        raise typer.Exit(1)

    app_id = project_id + "-" + app_name

    # Parse --since parameter if provided
    last_log_timestamp = None
    if since:
        last_log_timestamp = parse_since_timestamp(since)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Fetching logs...", total=None)

            while True:
                progress.update(task, description="Fetching logs...")

                logs_data, last_log_timestamp = fetch_logs(
                    project_id, app_id, last_log_timestamp=last_log_timestamp
                )

                if logs_data:
                    progress.refresh()
                    display_logs(logs_data.get("logs", []))
                else:
                    # Optionally, print "No new logs." if desired
                    pass

                if no_follow:
                    break

                # Wait for a few seconds before making another request
                progress.update(task, description="Listening for new logs...")
                time.sleep(5)

    except KeyboardInterrupt:
        console.print("\n[red]Stopped watching logs.[/red]")
        raise typer.Exit(0)


def display_logs(logs_data: List[LogEntry]):
    """
    Display logs in a table format.

    Args:
        logs_data (List[LogEntry]): A list of log entries.
    """
    if logs_data:
        table = Table(box=box.SIMPLE)
        table.add_column("Timestamp", style="cyan")
        table.add_column("Message", style="white")

        for log_entry in logs_data:
            timestamp = log_entry.get("timestamp", "")
            log_line = log_entry.get("logLine", "").rstrip()
            table.add_row(timestamp, log_line)

        console.print(table)


def fetch_logs(
    project_id: str,
    app_id: str,
    run_id: Optional[str] = None,
    last_log_timestamp: Optional[str] = None,
) -> Tuple[LogsResponse, Optional[str]]:
    """
    Fetch logs for the specified app or run.

    Args:
        project_id (str): The project ID.
        app_id (str): The application ID.
        run_id (Optional[str]): The run ID for fetching specific logs (if applicable).
        last_log_timestamp (Optional[str]): The timestamp after which to fetch logs.

    Returns:
        Tuple[List[Dict], Optional[str]]: A tuple containing the list of log entries and the latest timestamp.
    """
    # Prepare query parameters
    query_params = {}
    if last_log_timestamp:
        query_params["afterDate"] = last_log_timestamp
    if run_id:
        query_params["runId"] = run_id

    # Build the URL with query parameters
    url = f"v2/projects/{project_id}/apps/{app_id}/logs"
    if query_params:
        url += "?" + urlencode(query_params)

    # Make the GET request without a request body
    logs_response = cerebrium_request("GET", url, requires_auth=True)

    if logs_response is None:
        cerebrium_log(
            level="ERROR",
            message=f"There was an error getting the logs of app {app_id}. Please login and try again.\nIf the problem persists, please contact support.",
            prefix="",
        )
        bugsnag.notify(
            Exception("There was an error getting app logs"),
            meta_data={"appId": app_id, "runId": run_id},
            severity="error",
        )
        raise typer.Exit(1)

    if logs_response.status_code == 204:
        return LogsResponse(logs=[], nextPageToken=None, hasMore=False), last_log_timestamp

    if logs_response.status_code != 200:
        try:
            message = logs_response.json().get("message", None) or logs_response.json()
        except Exception:
            message = logs_response.text
        cerebrium_log(
            level="ERROR",
            message=f"There was an error getting the logs of app {app_id}.\n{message}",
            prefix="",
        )
        bugsnag.notify(
            Exception("There was an error getting app logs"),
            meta_data={"appId": app_id, "runId": run_id},
            severity="error",
        )
        raise typer.Exit(1)

    logs_data = logs_response.json()

    # Update the last_log_timestamp to the latest timestamp
    if logs_data and logs_data.get("logs"):
        last_log_timestamp = logs_data.get("logs", [])[-1].get("timestamp", last_log_timestamp)

    return logs_data, last_log_timestamp
