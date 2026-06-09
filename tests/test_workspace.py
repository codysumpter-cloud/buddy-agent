import json
from pathlib import Path

from buddy_agent.cli_workspace import run_workspace_command
from buddy_agent.workspace import init_buddy_workspace, workspace_status, write_workspace_item


def test_init_buddy_workspace_creates_playground_structure(tmp_path: Path):
    result = init_buddy_workspace(tmp_path)

    workspace = tmp_path / ".buddy" / "playground"
    assert result.workspace == workspace
    assert (workspace / "manifest.json").exists()
    assert (workspace / "permissions.json").exists()
    assert (workspace / "outbox" / "email_drafts").is_dir()
    assert (workspace / "art" / "requests").is_dir()
    assert (workspace / "browser" / "research_notes").is_dir()
    assert (workspace / "code" / "tasks").is_dir()

    manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["mode"] == "local_reviewable_workspace"
    assert "code_writing" in manifest["passive_capabilities"]
    assert "create_calendar_event" in manifest["requires_user_approval"]


def test_workspace_status_counts_created_items(tmp_path: Path):
    init_buddy_workspace(tmp_path)
    write_workspace_item(
        tmp_path,
        kind="email",
        title="Hello",
        body="Draft body",
    )
    write_workspace_item(
        tmp_path,
        kind="art",
        title="Sprite",
        body="Pixel mascot idle frame",
    )

    status = workspace_status(tmp_path)

    assert status.exists is True
    assert status.item_counts["email"] == 1
    assert status.item_counts["art"] == 1
    assert status.item_counts["message"] == 0


def test_workspace_items_are_reviewable_drafts(tmp_path: Path):
    email = write_workspace_item(
        tmp_path,
        kind="email",
        title="Follow Up",
        body="Thanks for the update.",
    )
    calendar = write_workspace_item(
        tmp_path,
        kind="calendar",
        title="Planning Call",
        body="Tomorrow at 3 PM",
    )
    code = write_workspace_item(
        tmp_path,
        kind="code",
        title="Add Browser Panel",
        body="Build a web surface shell.",
    )

    assert email.requires_approval is True
    assert calendar.requires_approval is True
    assert code.requires_approval is False
    assert email.path.suffix == ".md"
    assert calendar.path.suffix == ".json"
    assert "requires_user_approval: yes" in email.path.read_text(encoding="utf-8")


def test_workspace_cli_creates_code_task(tmp_path: Path):
    exit_code = run_workspace_command(
        [
            "code-task",
            str(tmp_path),
            "Build browser shell",
            "Create a draft plan for the browser surface.",
        ]
    )

    assert exit_code == 0
    tasks = list((tmp_path / ".buddy" / "playground" / "code" / "tasks").glob("*.md"))
    assert len(tasks) == 1
    assert "Build browser shell" in tasks[0].read_text(encoding="utf-8")
