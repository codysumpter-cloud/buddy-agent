"""Public-safe KnowledgeVault events for persistent Buddy tasks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from buddy_agent.control_plane.knowledge_vault import KnowledgeVaultEmitter

from .models import TaskRecord, TaskStatus

ACTION_EVENT_TYPES = {
    "buddy.task.create": "task_created",
    "buddy.task.complete": "task_completed",
}


@dataclass(frozen=True)
class TaskEventResult:
    """Outcome returned to the caller without leaking local paths or task content."""

    configured: bool
    emitted: bool
    event_type: str | None = None
    event_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "emitted": self.emitted,
            "event_type": self.event_type,
            "event_id": self.event_id,
            "error": self.error,
        }


class KnowledgeVaultTaskEventSink:
    """Emit sanitized lifecycle transitions into a configured Vegapunk inbox."""

    def __init__(self, inbox_path: Path) -> None:
        self.emitter = KnowledgeVaultEmitter(inbox_path)

    def emit(
        self,
        *,
        action: str,
        previous_status: TaskStatus | None,
        task: TaskRecord,
        summary: str,
    ) -> TaskEventResult:
        event_type = ACTION_EVENT_TYPES.get(action, "task_state_changed")
        counts = Counter(step.status for step in task.plan)
        payload: dict[str, Any] = {
            "class": "task",
            "task_id": task.id,
            "previous_status": previous_status,
            "status": task.status,
            "risk": task.risk,
            "revision": task.revision,
            "approval": {
                "required": task.approval.required,
                "decision": task.approval.decision,
            },
            "step_counts": {
                "pending": counts.get("pending", 0),
                "running": counts.get("running", 0),
                "completed": counts.get("completed", 0),
                "failed": counts.get("failed", 0),
                "skipped": counts.get("skipped", 0),
            },
            "receipt_count": len(task.receipts),
            "summary": summary,
            "action": action,
        }
        try:
            event = self.emitter.build_event(
                event_type=event_type,
                object_id=f"{task.id}-r{task.revision}",
                payload=payload,
                source_ref=f"buddy-agent://tasks/{task.id}",
            )
            self.emitter.write(event)
        except (OSError, ValueError):
            return TaskEventResult(
                configured=True,
                emitted=False,
                event_type=event_type,
                error="task event emission failed",
            )
        return TaskEventResult(
            configured=True,
            emitted=True,
            event_type=event.event_type,
            event_id=event.event_id,
        )
