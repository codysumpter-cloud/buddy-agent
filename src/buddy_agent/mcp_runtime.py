"""Composed Buddy MCP runtime.

The core server stays dependency-free and transport-focused. Optional local tool
families register here before the packaged executable starts serving requests.
"""

from __future__ import annotations

from . import mcp_server
from .mcp_events import register_task_event_hooks
from .mcp_game import register_game_tools
from .mcp_tasks import register_task_tools

register_task_tools()
register_task_event_hooks()
register_game_tools()


def main(argv: list[str] | None = None) -> int:
    return mcp_server.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
