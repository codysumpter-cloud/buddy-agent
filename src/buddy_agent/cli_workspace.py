"""CLI helpers for the local Buddy playground workspace."""

from __future__ import annotations

from .workspace import WorkspaceItemKind, init_buddy_workspace, workspace_status, write_workspace_item

WORKSPACE_CREATE_COMMANDS: dict[str, WorkspaceItemKind] = {
    "draft-email": "email",
    "draft-message": "message",
    "draft-calendar": "calendar",
    "art-request": "art",
    "browser-note": "browser",
    "code-task": "code",
    "file-note": "file",
}


def run_workspace_command(parts: list[str]) -> int:
    """Run Buddy playground workspace commands."""

    subcommand = parts[0] if parts else "status"
    project_path = parts[1] if len(parts) > 1 else "."

    if subcommand == "init":
        result = init_buddy_workspace(project_path)
        for line in result.summary_lines():
            print(line)
        return 0

    if subcommand == "status":
        print(workspace_status(project_path).to_json())
        return 0

    if subcommand in WORKSPACE_CREATE_COMMANDS:
        title = parts[2] if len(parts) > 2 else subcommand.replace("-", " ").title()
        body = " ".join(parts[3:]).strip() or title
        result = write_workspace_item(
            project_path,
            kind=WORKSPACE_CREATE_COMMANDS[subcommand],
            title=title,
            body=body,
        )
        for line in result.summary_lines():
            print(line)
        return 0

    print(
        "Usage: buddy-workspace "
        "[init|status|draft-email|draft-message|draft-calendar|art-request|"
        "browser-note|code-task|file-note] [project-path] [title] [body]"
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    """Run the standalone Buddy workspace CLI."""

    return run_workspace_command(argv or [])
