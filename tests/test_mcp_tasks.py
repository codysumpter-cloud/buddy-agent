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
    (project / "README.md").write_text("# Task tool test\n", encoding="utf-8")
    return mcp_server.BuddyMcpConfig(project_root=project, vault_root=vault)


def test_composed_registry_lists_task_tools(tmp_path: Path) -> None:
    response = mcp_server.handle_request(
        config(tmp_path),
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    assert response is not None
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert {
        "buddy.task.create",
        "buddy.task.list",
        "buddy.task.get",
        "buddy.task.plan",
        "buddy.task.approval",
        "buddy.task.start",
        "buddy.task.step",
        "buddy.task.complete",
        "buddy.task.cancel",
        "buddy.task.resume",
    } <= names


def test_mcp_task_round_trip_with_approval_and_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = config(tmp_path)
    monkeypatch.setenv("BUDDY_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setenv("BUDDY_RECEIPTS_DIR", str(tmp_path / "receipts"))

    created = mcp_server.call_tool(
        selected,
        "buddy.task.create",
        {"objective": "Repair the repository", "risk": "repo-mutation"},
    )
    task_id = created["id"]
    assert created["project_root"] == str(selected.project_root)

    planned = mcp_server.call_tool(
        selected,
        "buddy.task.plan",
        {
            "task_id": task_id,
            "steps": ["Inspect", "Patch", "Verify"],
            "verification": ["pytest -q"],
        },
    )
    assert planned["status"] == "awaiting_approval"

    with pytest.raises(mcp_server.McpToolError, match="cannot start"):
        mcp_server.call_tool(selected, "buddy.task.start", {"task_id": task_id})

    approved = mcp_server.call_tool(
        selected,
        "buddy.task.approval",
        {
            "task_id": task_id,
            "approved": True,
            "decided_by": "Cody",
            "note": "Approved for this task",
        },
    )
    assert approved["status"] == "planned"
    assert approved["approval"]["decided_by"] == "Cody"

    running = mcp_server.call_tool(selected, "buddy.task.start", {"task_id": task_id})
    assert running["status"] == "running"

    for step_id, artifacts in (
        ("step-1", []),
        ("step-2", []),
        ("step-3", ["artifacts/pytest.log"]),
    ):
        mcp_server.call_tool(
            selected,
            "buddy.task.step",
            {
                "task_id": task_id,
                "step_id": step_id,
                "completed": True,
                "artifact_paths": artifacts,
            },
        )

    completed = mcp_server.call_tool(
        selected,
        "buddy.task.complete",
        {"task_id": task_id, "summary": "Repository repaired and verified"},
    )
    assert completed["status"] == "completed"

    fetched = mcp_server.call_tool(selected, "buddy.task.get", {"task_id": task_id})
    assert fetched["revision"] == completed["revision"]
    listed = mcp_server.call_tool(selected, "buddy.task.list", {})
    assert listed["count"] == 1

    receipt_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / "receipts").glob("*.jsonl")
    )
    assert "Repair the repository" not in receipt_text
    assert "Approved for this task" not in receipt_text
    assert "task.complete" in receipt_text


def test_tool_call_returns_safe_structured_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = config(tmp_path)
    monkeypatch.setenv("BUDDY_TASKS_DIR", str(tmp_path / "tasks"))
    response = mcp_server.handle_request(
        selected,
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "buddy.task.get",
                "arguments": {"task_id": "task-aaaaaaaaaaaaaaaaaaaaaaaa"},
            },
        },
    )
    assert response is not None
    assert response["result"]["isError"] is True
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["ok"] is False
    assert "unknown Buddy task" in payload["error"]


def test_packaged_self_test_counts_extensions(capsys: pytest.CaptureFixture[str]) -> None:
    assert mcp_main(["--self-test"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["tool_count"] >= 16
