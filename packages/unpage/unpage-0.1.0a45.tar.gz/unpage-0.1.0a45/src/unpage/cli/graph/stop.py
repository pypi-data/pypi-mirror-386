import os
import signal
import sys

from unpage.cli.graph._app import graph_app
from unpage.cli.graph._background import cleanup_pid_file, get_pid_file, is_process_running
from unpage.config import manager
from unpage.telemetry import client as telemetry
from unpage.telemetry import prepare_profile_for_telemetry


@graph_app.command
async def stop() -> None:
    """Stop running graph build"""
    active_profile = manager.get_active_profile()
    await telemetry.send_event(
        {
            "command": "graph stop",
            **prepare_profile_for_telemetry(active_profile),
        }
    )

    pid_file = get_pid_file()

    if not pid_file.exists():
        print("No graph build running")
        sys.exit(1)

    try:
        pid = int(pid_file.read_text().strip())
        if not is_process_running(pid):
            cleanup_pid_file()
            print("No graph build running")
            sys.exit(1)

        print(f"Stopping graph build (PID: {pid})...")
        os.kill(pid, signal.SIGTERM)
        print("Graph build stopped successfully")
        cleanup_pid_file()
    except (ValueError, ProcessLookupError):
        cleanup_pid_file()
        print("No graph build running")
        sys.exit(1)
