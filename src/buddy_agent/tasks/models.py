"""Persistent Buddy task lifecycle models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, cast

from buddy_agent.receipts.record import JSONValue

TaskStatus = Literal[
    "created",
    "awaiting_approval",
    "planned",
    "running",
    "cancelled",
    "completed",
    "failed",
]
StepStatus = Literal["pending", "running", "completed", "failed", "skipped"]
TaskRisk = Literal["read-only", "draft-only", "write", "repo-mutation", "destructive"]
ApprovalDecision = Literal["pending", "approved", "denied"]

TERMINAL_STATUSES: frozenset[TaskStatus] = frozenset({"cancelled", "completed", "failed"})
APPROVAL_REQUIRED_RISKS: frozenset[TaskRisk] = frozenset(
    {"write", "repo-mutation", "destructive"}
)


def utc_now() -> str:
    """Return a stable UTC timestamp string."""
    return datetime.now(UTC).isoformat()


@dataclass
class TaskStep:
    """One reviewable step in a Buddy task plan."""

    id: str
    title: str
    status: StepStatus = "pending"
    verification: list[str] = field(default_factory=list)
    artifact_paths: list[str] = field(default_factory=list)
    detail: str | None = None

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "verification": list(self.verification),
            "artifact_paths": list(self.artifact_paths),
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, value: dict[str, JSONValue]) -> TaskStep:
        return cls(
            id=str(value.get("id", "")),
            title=str(value.get("title", "")),
            status=cast(StepStatus, value.get("status", "pending")),
            verification=[str(item) for item in cast(list[JSONValue], value.get("verification", []))],
            artifact_paths=[
                str(item) for item in cast(list[JSONValue], value.get("artifact_paths", []))
            ],
            detail=str(value["detail"]) if value.get("detail") is not None else None,
        )


@dataclass
class ApprovalState:
    """Human approval gate for one task."""

    required: bool
    decision: ApprovalDecision = "pending"
    requested_at: str | None = None
    decided_at: str | None = None
    decided_by: str | None = None
    note: str | None = None

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "required": self.required,
            "decision": self.decision,
            "requested_at": self.requested_at,
            "decided_at": self.decided_at,
            "decided_by": self.decided_by,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, value: dict[str, JSONValue]) -> ApprovalState:
        return cls(
            required=bool(value.get("required", False)),
            decision=cast(ApprovalDecision, value.get("decision", "pending")),
            requested_at=(
                str(value["requested_at"]) if value.get("requested_at") is not None else None
            ),
            decided_at=str(value["decided_at"]) if value.get("decided_at") is not None else None,
            decided_by=str(value["decided_by"]) if value.get("decided_by") is not None else None,
            note=str(value["note"]) if value.get("note") is not None else None,
        )


@dataclass
class TaskRecord:
    """Serializable task state recovered across Buddy restarts."""

    id: str
    objective: str
    risk: TaskRisk
    status: TaskStatus = "created"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    project_root: str | None = None
    plan: list[TaskStep] = field(default_factory=list)
    approval: ApprovalState = field(default_factory=lambda: ApprovalState(required=False))
    result_summary: str | None = None
    failure: str | None = None
    receipts: list[str] = field(default_factory=list)
    revision: int = 1

    def touch(self) -> None:
        self.updated_at = utc_now()
        self.revision += 1

    def to_dict(self) -> dict[str, JSONValue]:
        return {
            "schema": "buddy.task.v1",
            "id": self.id,
            "objective": self.objective,
            "risk": self.risk,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_root": self.project_root,
            "plan": [step.to_dict() for step in self.plan],
            "approval": self.approval.to_dict(),
            "result_summary": self.result_summary,
            "failure": self.failure,
            "receipts": list(self.receipts),
            "revision": self.revision,
        }

    @classmethod
    def from_dict(cls, value: dict[str, JSONValue]) -> TaskRecord:
        raw_plan = cast(list[JSONValue], value.get("plan", []))
        raw_approval = value.get("approval", {})
        approval = ApprovalState.from_dict(
            cast(dict[str, JSONValue], raw_approval) if isinstance(raw_approval, dict) else {}
        )
        return cls(
            id=str(value.get("id", "")),
            objective=str(value.get("objective", "")),
            risk=cast(TaskRisk, value.get("risk", "read-only")),
            status=cast(TaskStatus, value.get("status", "created")),
            created_at=str(value.get("created_at", utc_now())),
            updated_at=str(value.get("updated_at", utc_now())),
            project_root=(
                str(value["project_root"]) if value.get("project_root") is not None else None
            ),
            plan=[
                TaskStep.from_dict(cast(dict[str, JSONValue], item))
                for item in raw_plan
                if isinstance(item, dict)
            ],
            approval=approval,
            result_summary=(
                str(value["result_summary"])
                if value.get("result_summary") is not None
                else None
            ),
            failure=str(value["failure"]) if value.get("failure") is not None else None,
            receipts=[str(item) for item in cast(list[JSONValue], value.get("receipts", []))],
            revision=int(cast(int | str, value.get("revision", 1))),
        )
