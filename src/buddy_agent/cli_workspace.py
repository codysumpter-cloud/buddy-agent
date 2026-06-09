"""Command line interface for Buddy Playground workspace."""

from __future__ import annotations

import sys

from .workspace import (
    init_buddy_workspace,
    parse_workspace_item_kind,
    workspace_status,
    write_workspace_item,
)

WORKSPACE_CREATE_COMMANDS: dict[str, str] = {
    "draft-email": "email",
    "draft-message": "message",
    "draft-calendar": "calendar",
    "art-request": "art",
    "browser-note": "browser",
    "code-task": "code",
    "file-note": "file",
}


def run_workspace_command(parts: list[str]) -> int:
    """Run a Buddy Playground workspace command."""

    subcommand = parts[0] if parts else "status"
    root = parts[1] if len(parts) > 1 else "."

    if subcommand == "init":
        init_result = init_buddy_workspace(root)
        for line in init_result.summary_lines():
            print(line)
        return 0

    if subcommand == "status":
        status = workspace_status(root)
        for line in status.summary_lines():
            print(line)
        return 0

    if subcommand in WORKSPACE_CREATE_COMMANDS:
        if len(parts) < 4:
            print(f"Usage: buddy-workspace {subcommand} <project-path> <title> <body>")
            return 2
        try:
            kind = parse_workspace_item_kind(WORKSPACE_CREATE_COMMANDS[subcommand])
        except ValueError as error:
            print(f"fail workspace: {error}")
            return 2
        item_result = write_workspace_item(
            root,
            kind=kind,
            title=parts[2],
            body=" ".join(parts[3:]),
        )
        for line in item_result.summary_lines():
            print(line)
        return 0

    print(
        "Usage: buddy-workspace "
        "[init|status|code-task|art-request|browser-note|draft-email|draft-message|draft-calendar|file-note] "
        "[project-path] [title] [body]"
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    """Run the Buddy Playground CLI."""

    return run_workspace_command(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
