import asyncio
import shutil
import sys

from unpage.cli.graph._app import graph_app
from unpage.cli.graph._background import get_log_file
from unpage.config import manager
from unpage.telemetry import client as telemetry
from unpage.telemetry import prepare_profile_for_telemetry


@graph_app.command
async def logs(
    *,
    follow: bool = False,
) -> None:
    """View graph build logs

    Parameters
    ----------
    follow
        Follow log output
    """
    active_profile = manager.get_active_profile()
    await telemetry.send_event(
        {
            "command": "graph logs",
            **prepare_profile_for_telemetry(active_profile),
            "follow": follow,
        }
    )
    log_file = get_log_file()
    tail_cmd = shutil.which("tail")
    if not tail_cmd:
        print("'tail' command not found. Please install it.")
        sys.exit(1)

    if not log_file.exists():
        print("No log file found")
        print(f"Expected location: {log_file}")
        sys.exit(1)

    if follow:
        print("Following logs (Ctrl+C to stop)")
        print(f"Log file: {log_file}")

        try:
            proc = await asyncio.create_subprocess_shell(f"{tail_cmd} -f {log_file!s}")
            await proc.wait()
        except KeyboardInterrupt:
            print("\nStopped following logs")
    else:
        print("Recent logs:")
        print(f"Log file: {log_file}")

        proc = await asyncio.create_subprocess_shell(f"{tail_cmd} -n 50 {log_file!s}")
        await proc.wait()
