from __future__ import annotations

import json
from pathlib import Path

import pytest

from buddy_agent import mcp_server
from buddy_agent.mcp_runtime import main as mcp_main


def config(tmp_path: Path) -> mcp_server.BuddyMcpConfig:
    project = tmp_path / "project"
    vault = tmp_path / "vault"
    project.mkdir()
    vault.mkdir()
    return mcp_server.BuddyMcpConfig(project_root=project, vault_root=vault)


def call(config: mcp_server.BuddyMcpConfig, name: str, arguments: dict[str, object]) -> dict[str, object]:
    return mcp_server.call_tool(config, name, arguments)


def event_files(inbox: Path) -> list[Path]:
    return sorted(inbox.glob("*.json"))


def read_events(inbox: Path) -> list[dict[str, object]]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in event_files(inbox)]


def test_mcp_task_lifecycle_emits_public_safe_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = config(tmp_path)
    tasks = tmp_path / "tasks"
    receipts = tmp_path / "receipts"
    inbox = tmp_path / "knowledge-vault" / "inbox" / "events"
    monkeypatch.setenv("BUDDY_TASKS_DIR", str(tasks))
    monkeypatch.setenv("BUDDY_RECEIPTS_DIR", str(receipts))
    monkeypatch.setenv("BUDDY_VAULT_INBOX", str(inbox))

    created = call(
        selected,
        "buddy.task.create",
        {
            "objective": "Repair private/customer/path with access_token=do-not-store",
            "risk": "repo-mutation",
        },
    )
    task_id = str(created["id"])
    assert created["memory_event"]["configured"] is True  # type: ignore[index]
    assert created["memory_event"]["emitted"] is True  # type: ignore[index]

    planned = call(
        selected,
        "buddy.task.plan",
        {
            "task_id": task_id,
            "steps": ["Inspect private details", "Run tests"],
            "verification": ["pytest -q"],
        },
    )
    assert planned["status"] == "awaiting_approval"

    approved = call(
        selected,
        "buddy.task.approval",
        {
            "task_id": task_id,
            "approved": True,
            "decided_by": "Cody",
            "note": "Contains private customer context and password=hunter2",
        },
    )
    assert approved["approval"]["decision"] == "approved"  # type: ignore[index]
    call(selected, "buddy.task.start", {"task_id": task_id})
    call(
        selected,
        "buddy.task.step",
        {"task_id": task_id, "step_id": "step-1", "completed": True},
    )
    call(
        selected,
        "buddy.task.step",
        {
            "task_id": task_id,
            "step_id": "step-2",
            "completed": True,
            "artifact_paths": ["private/build.log"],
        },
    )
    completed = call(
        selected,
        "buddy.task.complete",
        {"task_id": task_id, "summary": "Verified completion"},
    )
    assert completed["memory_event"]["event_type"] == "task_completed"  # type: ignore[index]

    events = read_events(inbox)
    assert [event["event_type"] for event in events].count("task_created") == 1
    assert [event["event_type"] for event in events].count("task_completed") == 1
    assert [event["event_type"] for event in events].count("task_state_changed") >= 5

    serialized = json.dumps(events)
    for forbidden in (
        "Repair private/customer/path",
        "do-not-store",
        "Inspect private details",
        "private customer context",
        "hunter2",
        "private/build.log",
        str(selected.project_root),
        str(inbox),
    ):
        assert forbidden not in serialized

    payloads = [event["payload"] for event in events]
    assert all(payload["task_id"] == task_id for payload in payloads)  # type: ignore[index]
    assert all("step_counts" in payload for payload in payloads)  # type: ignore[operator]
    assert all("objective" not in payload for payload in payloads)  # type: ignore[operator]
    assert all("source_ref" in payload for payload in payloads)  # type: ignore[operator]


def test_unconfigured_inbox_is_explicit_without_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = config(tmp_path)
    monkeypatch.setenv("BUDDY_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setenv("BUDDY_RECEIPTS_DIR", str(tmp_path / "receipts"))
    monkeypatch.delenv("BUDDY_VAULT_INBOX", raising=False)

    created = call(selected, "buddy.task.create", {"objective": "Read-only task"})
    assert created["memory_event"] == {
        "configured": False,
        "emitted": False,
        "event_type": None,
        "event_id": None,
        "error": None,
    }
    assert not list(tmp_path.rglob("evt-*.json"))


def test_event_write_failure_does_not_erase_persisted_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = config(tmp_path)
    tasks = tmp_path / "tasks"
    invalid_inbox = tmp_path / "not-a-directory"
    invalid_inbox.write_text("occupied", encoding="utf-8")
    monkeypatch.setenv("BUDDY_TASKS_DIR", str(tasks))
    monkeypatch.setenv("BUDDY_RECEIPTS_DIR", str(tmp_path / "receipts"))
    monkeypatch.setenv("BUDDY_VAULT_INBOX", str(invalid_inbox))

    created = call(selected, "buddy.task.create", {"objective": "Keep durable local state"})
    assert created["memory_event"]["emitted"] is False  # type: ignore[index]
    assert created["memory_event"]["error"] == "task event emission failed"  # type: ignore[index]
    task_id = str(created["id"])
    fetched = call(selected, "buddy.task.get", {"task_id": task_id})
    assert fetched["objective"] == "Keep durable local state"


def test_packaged_runtime_registers_event_hooks(capsys: pytest.CaptureFixture[str]) -> None:
    assert mcp_main(["--self-test"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["tool_count"] >= 16
