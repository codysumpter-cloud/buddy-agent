"""Structured envelopes for Buddy + Lil' Buddy orchestration."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Literal, TypeAlias

SafetyClass: TypeAlias = Literal["low", "medium", "high", "blocked"]
ResultStatus: TypeAlias = Literal["complete", "partial", "blocked", "failed"]
ReviewStatus: TypeAlias = Literal[
    "approved",
    "approved_with_notes",
    "revise",
    "escalate",
    "block",
]
ToolContractType: TypeAlias = Literal[
    "read-only",
    "draft-only",
    "local-execution",
    "repo-mutation",
    "device-observation",
    "device-action",
    "external-action",
]

TASK_SCHEMA_VERSION = "buddy.task.v1"
RESULT_SCHEMA_VERSION = "buddy.result.v1"
REVIEW_SCHEMA_VERSION = "buddy.review.v1"


def stable_task_id(user_intent: str, delegated_scope: str) -> str:
    """Return a deterministic local task id for demos and tests."""
    digest = hashlib.sha256(f"{user_intent}\n{delegated_scope}".encode("utf-8")).hexdigest()
    return f"task-{digest[:12]}"


@dataclass(frozen=True)
class ToolContract:
    """A tool permission granted to Lil' Buddy by Buddy."""

    name: str
    contract: ToolContractType
    description: str
    requires_approval: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return asdict(self)


@dataclass(frozen=True)
class TaskEnvelope:
    """A scoped work packet from Buddy to Lil' Buddy."""

    task_id: str
    orchestrator: str
    worker: str
    user_intent: str
    delegated_scope: str
    constraints: tuple[str, ...]
    approved_tools: tuple[ToolContract, ...]
    safety_class: SafetyClass
    expected_output: str = "buddy.result.v1 envelope"
    review_required: bool = True
    schema_version: str = TASK_SCHEMA_VERSION

    @classmethod
    def build(
        cls,
        *,
        user_intent: str,
        delegated_scope: str,
        constraints: tuple[str, ...],
        approved_tools: tuple[ToolContract, ...],
        safety_class: SafetyClass,
        orchestrator: str = "Buddy",
        worker: str = "Lil Buddy",
    ) -> TaskEnvelope:
        """Build a task envelope with a deterministic task id."""
        return cls(
            task_id=stable_task_id(user_intent, delegated_scope),
            orchestrator=orchestrator,
            worker=worker,
            user_intent=user_intent,
            delegated_scope=delegated_scope,
            constraints=constraints,
            approved_tools=approved_tools,
            safety_class=safety_class,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "orchestrator": self.orchestrator,
            "worker": self.worker,
            "user_intent": self.user_intent,
            "delegated_scope": self.delegated_scope,
            "constraints": list(self.constraints),
            "approved_tools": [tool.to_dict() for tool in self.approved_tools],
            "safety_class": self.safety_class,
            "expected_output": self.expected_output,
            "review_required": self.review_required,
        }


@dataclass(frozen=True)
class ResultEnvelope:
    """Structured result returned by Lil' Buddy."""

    task_id: str
    worker: str
    status: ResultStatus
    summary: str
    findings: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    open_questions: tuple[str, ...] = ()
    tool_calls: tuple[str, ...] = ()
    needs_buddy_review: bool = True
    schema_version: str = RESULT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "worker": self.worker,
            "status": self.status,
            "summary": self.summary,
            "findings": list(self.findings),
            "artifacts": list(self.artifacts),
            "risks": list(self.risks),
            "open_questions": list(self.open_questions),
            "tool_calls": list(self.tool_calls),
            "needs_buddy_review": self.needs_buddy_review,
        }


@dataclass(frozen=True)
class ReviewEnvelope:
    """Buddy's review of a Lil' Buddy result."""

    task_id: str
    reviewer: str
    status: ReviewStatus
    approved_findings: tuple[str, ...]
    notes: tuple[str, ...] = ()
    escalation_required: bool = False
    schema_version: str = REVIEW_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "reviewer": self.reviewer,
            "status": self.status,
            "approved_findings": list(self.approved_findings),
            "notes": list(self.notes),
            "escalation_required": self.escalation_required,
        }


@dataclass(frozen=True)
class OrchestrationTrace:
    """A complete local orchestration trace for demo output."""

    user_intent: str
    buddy_plan: tuple[str, ...]
    task: TaskEnvelope
    result: ResultEnvelope
    review: ReviewEnvelope
    final_response: str
    durable_memory_targets: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "user_intent": self.user_intent,
            "buddy_plan": list(self.buddy_plan),
            "task": self.task.to_dict(),
            "result": self.result.to_dict(),
            "review": self.review.to_dict(),
            "final_response": self.final_response,
            "durable_memory_targets": list(self.durable_memory_targets),
        }
