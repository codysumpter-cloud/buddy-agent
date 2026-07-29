"""Guarded persistent lifecycle for Buddy tasks.

This module manages state, approval, receipts, and restart recovery. It does not
execute repository commands; a future sandbox executor must claim and complete
steps through this lifecycle rather than bypassing it.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import cast

from buddy_agent.receipts import ReceiptRecord, ReceiptWriter

from .models import (
    APPROVAL_REQUIRED_RISKS,
    TERMINAL_STATUSES,
    ApprovalState,
    TaskRecord,
    TaskRisk,
    TaskStatus,
    TaskStep,
    utc_now,
)
from .store import TaskStore


class TaskTransitionError(ValueError):
    """Raised when a requested lifecycle transition is unsafe or invalid."""


def _task_id() -> str:
    return f"task-{uuid.uuid4().hex[:24]}"


def _receipt_status(status: TaskStatus) -> str:
    if status == "completed":
        return "ok"
    if status == "awaiting_approval":
        return "review"
    if status in {"cancelled", "failed"}:
        return "error"
    return "review"


class TaskRuntime:
    """Create and transition local Buddy task records."""

    def __init__(
        self,
        store: TaskStore | None = None,
        receipt_writer: ReceiptWriter | None = None,
    ) -> None:
        self.store = store or TaskStore()
        self.receipt_writer = receipt_writer

    def _persist(self, task: TaskRecord, action: str, summary: str) -> TaskRecord:
        task.touch()
        state_path = self.store.save(task)
        if self.receipt_writer is not None:
            receipt = ReceiptRecord(
                action=action,
                status=cast("Literal['ok', 'error', 'review', 'deny']", _receipt_status(task.status)),
                summary=summary,
                metadata={
                    "task_id": task.id,
                    "task_status": task.status,
                    "risk": task.risk,
                    "revision": task.revision,
                    "state_path": str(state_path),
                },
            )
            receipt_path = self.receipt_writer.write(receipt)
            task.receipts.append(str(receipt_path))
            self.store.save(task)
        return task

    def create(
        self,
        objective: str,
        *,
        risk: TaskRisk = "read-only",
        project_root: Path | None = None,
    ) -> TaskRecord:
        """Create a task without inventing an execution plan."""
        clean = objective.strip()
        if not clean:
            raise TaskTransitionError("task objective cannot be empty")
        task = TaskRecord(
            id=_task_id(),
            objective=clean,
            risk=risk,
            project_root=str(project_root.expanduser().resolve()) if project_root else None,
        )
        return self._persist(task, "task.create", "Buddy task created")

    def plan(
        self,
        task_id: str,
        steps: list[str],
        *,
        verification: list[str] | None = None,
    ) -> TaskRecord:
        """Attach a reviewable plan and request approval when risk requires it."""
        task = self.store.load(task_id)
        if task.status not in {"created", "planned", "awaiting_approval", "failed", "cancelled"}:
            raise TaskTransitionError(f"cannot plan task from status {task.status}")
        clean_steps = [step.strip() for step in steps if step.strip()]
        if not clean_steps:
            raise TaskTransitionError("task plan must include at least one step")
        checks = [item.strip() for item in verification or [] if item.strip()]
        task.plan = [
            TaskStep(
                id=f"step-{index + 1}",
                title=title,
                verification=list(checks) if index == len(clean_steps) - 1 else [],
            )
            for index, title in enumerate(clean_steps)
        ]
        task.result_summary = None
        task.failure = None
        if task.risk in APPROVAL_REQUIRED_RISKS:
            task.status = "awaiting_approval"
            task.approval = ApprovalState(
                required=True,
                decision="pending",
                requested_at=utc_now(),
            )
            summary = "Buddy task plan is waiting for human approval"
        else:
            task.status = "planned"
            task.approval = ApprovalState(required=False, decision="approved")
            summary = "Buddy task plan is ready"
        return self._persist(task, "task.plan", summary)

    def respond_approval(
        self,
        task_id: str,
        *,
        approved: bool,
        decided_by: str,
        note: str | None = None,
    ) -> TaskRecord:
        """Approve or deny a pending task with an attributable human decision."""
        task = self.store.load(task_id)
        if task.status != "awaiting_approval" or task.approval.decision != "pending":
            raise TaskTransitionError("task does not have a pending approval request")
        actor = decided_by.strip()
        if not actor:
            raise TaskTransitionError("approval decision requires decided_by")
        task.approval.decision = "approved" if approved else "denied"
        task.approval.decided_at = utc_now()
        task.approval.decided_by = actor
        task.approval.note = note.strip() if note else None
        task.status = "planned" if approved else "cancelled"
        action = "task.approve" if approved else "task.deny"
        summary = "Buddy task approved" if approved else "Buddy task denied"
        return self._persist(task, action, summary)

    def start(self, task_id: str) -> TaskRecord:
        """Mark a planned task running without executing any commands itself."""
        task = self.store.load(task_id)
        if task.status != "planned":
            raise TaskTransitionError(f"cannot start task from status {task.status}")
        if task.approval.required and task.approval.decision != "approved":
            raise TaskTransitionError("task cannot start without required approval")
        task.status = "running"
        if task.plan:
            task.plan[0].status = "running"
        return self._persist(task, "task.start", "Buddy task started")

    def update_step(
        self,
        task_id: str,
        step_id: str,
        *,
        completed: bool,
        detail: str | None = None,
        artifact_paths: list[str] | None = None,
    ) -> TaskRecord:
        """Record worker progress without accepting unverified completion claims."""
        task = self.store.load(task_id)
        if task.status != "running":
            raise TaskTransitionError("steps can only be updated while a task is running")
        selected = next((step for step in task.plan if step.id == step_id), None)
        if selected is None:
            raise TaskTransitionError(f"unknown task step: {step_id}")
        selected.status = "completed" if completed else "failed"
        selected.detail = detail.strip() if detail else None
        selected.artifact_paths = [path.strip() for path in artifact_paths or [] if path.strip()]
        if not completed:
            task.status = "failed"
            task.failure = selected.detail or f"step failed: {selected.title}"
            return self._persist(task, "task.step.fail", "Buddy task step failed")
        pending = next((step for step in task.plan if step.status == "pending"), None)
        if pending is not None:
            pending.status = "running"
        return self._persist(task, "task.step.complete", "Buddy task step completed")

    def complete(self, task_id: str, summary: str) -> TaskRecord:
        """Complete only when every planned step has executable evidence fields satisfied."""
        task = self.store.load(task_id)
        if task.status != "running":
            raise TaskTransitionError(f"cannot complete task from status {task.status}")
        incomplete = [step.id for step in task.plan if step.status != "completed"]
        if incomplete:
            raise TaskTransitionError(f"cannot complete task with unfinished steps: {', '.join(incomplete)}")
        missing_artifacts = [
            step.id
            for step in task.plan
            if step.verification and not step.artifact_paths
        ]
        if missing_artifacts:
            raise TaskTransitionError(
                "cannot complete verified steps without artifact paths: " + ", ".join(missing_artifacts)
            )
        clean = summary.strip()
        if not clean:
            raise TaskTransitionError("completion summary cannot be empty")
        task.status = "completed"
        task.result_summary = clean
        task.failure = None
        return self._persist(task, "task.complete", "Buddy task completed with recorded evidence")

    def fail(self, task_id: str, reason: str) -> TaskRecord:
        task = self.store.load(task_id)
        if task.status in TERMINAL_STATUSES:
            raise TaskTransitionError(f"cannot fail task from terminal status {task.status}")
        clean = reason.strip()
        if not clean:
            raise TaskTransitionError("failure reason cannot be empty")
        task.status = "failed"
        task.failure = clean
        for step in task.plan:
            if step.status == "running":
                step.status = "failed"
                step.detail = clean
        return self._persist(task, "task.fail", "Buddy task failed")

    def cancel(self, task_id: str, reason: str | None = None) -> TaskRecord:
        task = self.store.load(task_id)
        if task.status in TERMINAL_STATUSES:
            raise TaskTransitionError(f"cannot cancel task from terminal status {task.status}")
        task.status = "cancelled"
        task.failure = reason.strip() if reason else "cancelled by operator"
        for step in task.plan:
            if step.status in {"pending", "running"}:
                step.status = "skipped"
        return self._persist(task, "task.cancel", "Buddy task cancelled")

    def resume(self, task_id: str) -> TaskRecord:
        task = self.store.load(task_id)
        if task.status not in {"cancelled", "failed"}:
            raise TaskTransitionError(f"cannot resume task from status {task.status}")
        task.failure = None
        for step in task.plan:
            if step.status in {"failed", "skipped", "running"}:
                step.status = "pending"
                step.detail = None
        if task.approval.required and task.approval.decision != "approved":
            task.status = "awaiting_approval"
            task.approval.decision = "pending"
            task.approval.requested_at = utc_now()
            task.approval.decided_at = None
            task.approval.decided_by = None
        else:
            task.status = "planned" if task.plan else "created"
        return self._persist(task, "task.resume", "Buddy task resumed")
