import asyncio
import os
import shlex
import sys
import time
from collections import Counter

import anyio

from unpage.cli.graph._app import graph_app
from unpage.cli.graph._background import (
    check_and_create_lock,
    cleanup_pid_file,
    create_pid_file,
    get_log_file,
)
from unpage.config import manager
from unpage.knowledge import Graph
from unpage.plugins import PluginManager
from unpage.plugins.mixins import KnowledgeGraphMixin
from unpage.telemetry import client as telemetry
from unpage.telemetry import prepare_profile_for_telemetry


@graph_app.command
async def build(
    *,
    interval: int | None = None,
    background: bool = False,
) -> None:
    """Build a knowledge graph for your cloud infrastructure

    Parameters
    ----------
    interval
        Rebuild the graph continuously, pausing for the specified seconds between builds
    background
        Run in background and return immediately
    """
    # Check if already running
    if not check_and_create_lock():
        print("Graph build already running")
        print("Use 'unpage graph stop' to stop it if needed")
        sys.exit(1)

    if background:
        # Build command args for subprocess
        cmd = [a for a in sys.argv if a != "--background"]

        # Set up logging
        log_file = get_log_file()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Start subprocess with logging
        with log_file.open("w") as f:
            f.write("Starting graph build in background\n")
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write("=" * 50 + "\n\n")
            f.flush()

            await asyncio.create_subprocess_shell(
                shlex.join(cmd), stdout=f, stderr=asyncio.subprocess.STDOUT, start_new_session=True
            )

        print("Graph building started in background")
        print("Check progress: unpage graph logs --follow")
        print("Stop with: unpage graph stop")
        return

    async def _build_graph() -> None:
        await telemetry.send_event(
            {
                "command": "graph build - starting",
                **prepare_profile_for_telemetry(manager.get_active_profile()),
                "interval": interval,
                "background": background,
            }
        )
        print("Building graph...")

        start_time = time.perf_counter()

        graph = Graph()
        config = manager.get_active_profile_config()
        output_path = (manager.get_active_profile_directory() / "graph.json").resolve()
        plugin_manager = PluginManager(config)

        async with anyio.create_task_group() as tg:
            for plugin in plugin_manager.get_plugins_with_capability(KnowledgeGraphMixin):
                print(f"Populating graph with the {plugin.name} plugin...")
                tg.start_soon(plugin.populate_graph, graph)

        await graph.infer_edges()

        print(f"Saving graph to {output_path!s}...")
        await graph.save(output_path)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        edge_counts = Counter(
            [edge.properties["relationship_type"] async for edge in graph.iter_edges()]
        )
        node_counts = Counter([node.node_type async for node in graph.iter_nodes()])

        print("=== Summary ===")

        print("Edges:")
        for relationship_type, count in edge_counts.items():
            print(f"  {relationship_type}: {count}")
        print("Nodes:")
        for node_type, count in node_counts.items():
            print(f"  {node_type}: {count}")

        print(f"Graph built in {total_time:.2f} seconds")
        print(f"Graph saved to {output_path!s}")
        print("=== End Summary ===")

        await telemetry.send_event(
            {
                "command": "graph build - finished",
                **prepare_profile_for_telemetry(manager.get_active_profile()),
                "duration_seconds": total_time,
                "node_counts": node_counts,
                "edge_counts": edge_counts,
            }
        )

    try:
        create_pid_file(os.getpid())

        if interval:
            while True:
                await _build_graph()
                print(f"Sleeping for {interval} seconds before next build...")
                await anyio.sleep(interval)
        else:
            await _build_graph()
    finally:
        cleanup_pid_file()
