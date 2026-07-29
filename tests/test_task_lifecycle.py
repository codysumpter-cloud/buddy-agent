from __future__ import annotations

import json
from pathlib import Path

import pytest

from buddy_agent.receipts import ReceiptWriter
from buddy_agent.tasks import TaskRuntime, TaskStore, TaskTransitionError
from buddy_agent.tasks.cli import main as task_cli


def runtime(tmp_path: Path, *, receipts: bool = False) -> TaskRuntime:
    writer = ReceiptWriter(tmp_path / "receipts") if receipts else None
    return TaskRuntime(TaskStore(tmp_path / "tasks"), writer)


def test_read_only_task_survives_restart_and_completes_with_evidence(tmp_path: Path) -> None:
    first = runtime(tmp_path, receipts=True)
    created = first.create("Inspect and repair the parser", project_root=tmp_path)
    planned = first.plan(
        created.id,
        ["Inspect current behavior", "Implement smallest fix", "Run verification"],
        verification=["pytest -q", "ruff check ."],
    )
    assert planned.status == "planned"
    assert planned.approval.required is False

    second = runtime(tmp_path, receipts=True)
    recovered = second.store.load(created.id)
    assert recovered.objective == created.objective
    assert recovered.revision == planned.revision

    running = second.start(created.id)
    assert running.status == "running"
    assert running.plan[0].status == "running"

    second.update_step(created.id, "step-1", completed=True, detail="Inspected source")
    second.update_step(created.id, "step-2", completed=True, detail="Patched parser")
    second.update_step(
        created.id,
        "step-3",
        completed=True,
        detail="Checks passed",
        artifact_paths=["artifacts/pytest.log", "artifacts/ruff.log"],
    )
    completed = second.complete(created.id, "Parser fixed and verified")
    assert completed.status == "completed"
    assert completed.result_summary == "Parser fixed and verified"
    assert completed.receipts

    receipt_lines = []
    for path in (tmp_path / "receipts").glob("*.jsonl"):
        receipt_lines.extend(path.read_text(encoding="utf-8").splitlines())
    payloads = [json.loads(line) for line in receipt_lines]
    assert any(payload["action"] == "task.complete" for payload in payloads)
    assert all("Inspect and repair" not in json.dumps(payload) for payload in payloads)


def test_repo_mutation_requires_attributable_approval(tmp_path: Path) -> None:
    selected = runtime(tmp_path)
    task = selected.create("Update repository policy", risk="repo-mutation")
    planned = selected.plan(task.id, ["Change policy", "Validate generated files"])
    assert planned.status == "awaiting_approval"
    assert planned.approval.decision == "pending"

    with pytest.raises(TaskTransitionError, match="cannot start"):
        selected.start(task.id)

    approved = selected.respond_approval(
        task.id,
        approved=True,
        decided_by="Cody",
        note="Approved for this branch only",
    )
    assert approved.status == "planned"
    assert approved.approval.decided_by == "Cody"
    assert selected.start(task.id).status == "running"


def test_denied_task_is_cancelled_and_resume_requests_approval_again(tmp_path: Path) -> None:
    selected = runtime(tmp_path)
    task = selected.create("Change production config", risk="write")
    selected.plan(task.id, ["Prepare reviewed change"])
    denied = selected.respond_approval(task.id, approved=False, decided_by="operator")
    assert denied.status == "cancelled"
    assert denied.approval.decision == "denied"

    resumed = selected.resume(task.id)
    assert resumed.status == "awaiting_approval"
    assert resumed.approval.decision == "pending"
    assert resumed.approval.decided_by is None


def test_verified_completion_refuses_missing_artifacts(tmp_path: Path) -> None:
    selected = runtime(tmp_path)
    task = selected.create("Run a verified change")
    selected.plan(task.id, ["Run required checks"], verification=["pytest"])
    selected.start(task.id)
    selected.update_step(task.id, "step-1", completed=True, detail="claimed pass")
    with pytest.raises(TaskTransitionError, match="without artifact paths"):
        selected.complete(task.id, "done")


def test_failed_step_can_be_resumed_without_losing_identity(tmp_path: Path) -> None:
    selected = runtime(tmp_path)
    task = selected.create("Repair build")
    selected.plan(task.id, ["Run build", "Repair failure"])
    selected.start(task.id)
    failed = selected.update_step(task.id, "step-1", completed=False, detail="compiler error")
    assert failed.status == "failed"

    resumed = selected.resume(task.id)
    assert resumed.id == task.id
    assert resumed.status == "planned"
    assert all(step.status == "pending" for step in resumed.plan)


def test_cli_create_plan_and_status(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks = tmp_path / "cli-tasks"
    assert task_cli(["--tasks-dir", str(tasks), "create", "Document the API"]) == 0
    created = json.loads(capsys.readouterr().out)
    task_id = created["id"]

    assert (
        task_cli(
            [
                "--tasks-dir",
                str(tasks),
                "plan",
                task_id,
                "--step",
                "Inspect docs",
                "--step",
                "Write update",
            ]
        )
        == 0
    )
    planned = json.loads(capsys.readouterr().out)
    assert planned["status"] == "planned"

    assert task_cli(["--tasks-dir", str(tasks), "status", task_id]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["revision"] == planned["revision"]
