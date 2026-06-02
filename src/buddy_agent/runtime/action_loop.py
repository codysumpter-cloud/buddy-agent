"""Safe Buddy + Lil' Buddy action loop runtime primitives.

This module gives Buddy-Agent a native Orchestrator/Worker session model for the
public alpha. It intentionally implements only the safe v1 action surface.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, TypeAlias
from uuid import uuid4

from buddy_agent.receipts import ReceiptRecord, ReceiptWriter

RiskClass: TypeAlias = Literal["read-only", "draft-only", "write"]
RiskDecision: TypeAlias = Literal["allow", "confirm"]
AgentRole: TypeAlias = Literal["orchestrator", "worker"]
ActionStatus: TypeAlias = Literal[
    "delegated",
    "needs-review",
    "completed",
    "cancelled",
    "denied",
]
SessionStatus: TypeAlias = Literal["waiting-for-human", "running", "completed"]
WorkerReportStatus: TypeAlias = Literal["step-completed", "blocked", "needs-approval", "done"]
ActionType: TypeAlias = Literal[
    "browser.summarize",
    "memory.remember",
    "note.draft",
    "calendar.draft",
    "calendar.create",
]

ACTION_SCHEMA_VERSION = "2026-06-02.buddy-action.v1"
SESSION_SCHEMA_VERSION = "2026-06-02.buddy-agent-session.v1"
SAFE_DEFAULT_RISK_POLICY: Mapping[RiskClass, RiskDecision] = {
    "read-only": "allow",
    "draft-only": "allow",
    "write": "confirm",
}


def now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 form."""
    return datetime.now(UTC).isoformat()


def requires_human_approval(risk: RiskClass) -> bool:
    """Return whether a risk class must pause for human approval."""
    return SAFE_DEFAULT_RISK_POLICY[risk] == "confirm"


@dataclass(frozen=True)
class AgentProfile:
    """A runtime agent profile for Buddy or Lil' Buddy."""

    agent_id: str
    buddy_id: str
    role: AgentRole
    display_name: str
    can_talk_to_human: bool
    can_delegate: bool
    can_execute_tools: bool


@dataclass(frozen=True)
class BuddyAction:
    """Typed action draft accepted by the Buddy runtime."""

    id: str
    buddy_id: str
    title: str
    intent: str
    action_type: ActionType
    risk: RiskClass
    status: ActionStatus
    session_id: str
    delegation_id: str
    assigned_agent_id: str
    assigned_agent_role: AgentRole = "worker"
    schema_version: str = ACTION_SCHEMA_VERSION
    created_at: str = field(default_factory=now_iso)

    @classmethod
    def delegated(
        cls,
        *,
        buddy_id: str,
        title: str,
        intent: str,
        action_type: ActionType,
        risk: RiskClass,
        session_id: str,
        delegation_id: str,
        assigned_agent_id: str,
    ) -> "BuddyAction":
        """Create an action with the correct initial status."""
        status: ActionStatus = "needs-review" if requires_human_approval(risk) else "delegated"
        return cls(
            id=str(uuid4()),
            buddy_id=buddy_id,
            title=title,
            intent=intent,
            action_type=action_type,
            risk=risk,
            status=status,
            session_id=session_id,
            delegation_id=delegation_id,
            assigned_agent_id=assigned_agent_id,
        )


@dataclass(frozen=True)
class BuddyDelegation:
    """A bounded unit of work from Buddy to Lil' Buddy."""

    id: str
    session_id: str
    objective: str
    next_instruction: str
    orchestrator_agent_id: str
    worker_agent_id: str
    status: Literal["running", "blocked", "completed", "cancelled"]
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class WorkerReport:
    """A worker report back to Buddy after a step."""

    id: str
    session_id: str
    delegation_id: str
    worker_agent_id: str
    orchestrator_agent_id: str
    status: WorkerReportStatus
    summary: str
    completed_action_ids: tuple[str, ...] = ()
    produced_receipt_ids: tuple[str, ...] = ()
    proposed_next_instruction: str | None = None
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class BuddyReceipt:
    """A sanitized action-loop receipt."""

    id: str
    action_id: str
    session_id: str
    delegation_id: str
    agent_role: AgentRole
    status: Literal["completed", "cancelled", "denied"]
    title: str
    summary: str
    risk: RiskClass
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class BuddyAgentSession:
    """A Buddy-led session with one default Lil' Buddy worker."""

    id: str
    original_human_request: str
    orchestrator: AgentProfile
    worker: AgentProfile
    status: SessionStatus
    schema_version: str = SESSION_SCHEMA_VERSION
    created_at: str = field(default_factory=now_iso)


@dataclass(frozen=True)
class BuddyWorldState:
    """Observable game-like world state for the active session."""

    current_mission: str
    active_surface: str
    buddy_status: str
    lil_buddy_status: str
    active_tool: str | None = None
    visible_artifacts: tuple[str, ...] = ()
    recent_receipt_ids: tuple[str, ...] = ()


@dataclass
class BuddyActionLoopRuntime:
    """Local two-agent action loop with safe default policy gates."""

    receipt_writer: ReceiptWriter | None = None
    orchestrator: AgentProfile = field(
        default_factory=lambda: AgentProfile(
            agent_id="buddy-orchestrator-default",
            buddy_id="default",
            role="orchestrator",
            display_name="Buddy",
            can_talk_to_human=True,
            can_delegate=True,
            can_execute_tools=False,
        )
    )
    worker: AgentProfile = field(
        default_factory=lambda: AgentProfile(
            agent_id="lil-buddy-worker-default",
            buddy_id="default",
            role="worker",
            display_name="Lil' Buddy",
            can_talk_to_human=False,
            can_delegate=False,
            can_execute_tools=True,
        )
    )
    session: BuddyAgentSession | None = None
    delegations: list[BuddyDelegation] = field(default_factory=list)
    reports: list[WorkerReport] = field(default_factory=list)
    receipts: list[BuddyReceipt] = field(default_factory=list)
    world_state: BuddyWorldState = field(
        default_factory=lambda: BuddyWorldState(
            current_mission="No active mission.",
            active_surface="browser",
            buddy_status="waiting for mission",
            lil_buddy_status="ready for delegated work",
        )
    )

    def start_session(self, original_human_request: str) -> BuddyAgentSession:
        """Start a Buddy-led session and reset loop-local state."""
        request = original_human_request.strip() or "Continue from the current Buddy context."
        session = BuddyAgentSession(
            id=str(uuid4()),
            original_human_request=request,
            orchestrator=self.orchestrator,
            worker=self.worker,
            status="running",
        )
        self.session = session
        self.delegations.clear()
        self.reports.clear()
        self.receipts.clear()
        self.world_state = BuddyWorldState(
            current_mission=request,
            active_surface="browser",
            buddy_status="owning the mission",
            lil_buddy_status="ready for delegated work",
            visible_artifacts=("session started",),
        )
        return session

    def delegate(
        self,
        *,
        title: str,
        instruction: str,
        action_type: ActionType,
        risk: RiskClass,
    ) -> BuddyAction:
        """Create a delegation and matching action for Lil' Buddy."""
        session = self.session or self.start_session("Continue from the current Buddy context.")
        needs_review = requires_human_approval(risk)
        delegation = BuddyDelegation(
            id=str(uuid4()),
            session_id=session.id,
            objective=title,
            next_instruction=instruction,
            orchestrator_agent_id=self.orchestrator.agent_id,
            worker_agent_id=self.worker.agent_id,
            status="blocked" if needs_review else "running",
        )
        self.delegations.append(delegation)
        action = BuddyAction.delegated(
            buddy_id=session.orchestrator.buddy_id,
            title=title,
            intent=instruction,
            action_type=action_type,
            risk=risk,
            session_id=session.id,
            delegation_id=delegation.id,
            assigned_agent_id=self.worker.agent_id,
        )
        self.world_state = BuddyWorldState(
            current_mission=session.original_human_request,
            active_surface=_surface_for_action(action_type),
            active_tool=action_type,
            buddy_status="approval needed" if needs_review else "delegating",
            lil_buddy_status="paused" if needs_review else "working",
            visible_artifacts=(f"delegated: {title}", *self.world_state.visible_artifacts[:11]),
            recent_receipt_ids=self.world_state.recent_receipt_ids,
        )
        return action

    def complete_action(self, action: BuddyAction, *, summary: str | None = None) -> WorkerReport:
        """Record a completed worker step and emit a receipt."""
        receipt = self._record_receipt(
            action,
            status="completed",
            summary=summary or _receipt_summary(action.action_type),
        )
        report = WorkerReport(
            id=str(uuid4()),
            session_id=action.session_id,
            delegation_id=action.delegation_id,
            worker_agent_id=self.worker.agent_id,
            orchestrator_agent_id=self.orchestrator.agent_id,
            status="step-completed",
            summary=f"Lil' Buddy completed {action.title} and reported back to Buddy.",
            completed_action_ids=(action.id,),
            produced_receipt_ids=(receipt.id,),
            proposed_next_instruction="Buddy can continue from the original mission.",
        )
        self.reports.append(report)
        self.world_state = BuddyWorldState(
            current_mission=self.world_state.current_mission,
            active_surface=_surface_for_action(action.action_type),
            active_tool=None,
            buddy_status="continuing mission",
            lil_buddy_status="reported step complete",
            visible_artifacts=(f"receipt: {receipt.title}", *self.world_state.visible_artifacts[:11]),
            recent_receipt_ids=(receipt.id, *self.world_state.recent_receipt_ids[:11]),
        )
        return report

    def deny_action(self, action: BuddyAction) -> WorkerReport:
        """Record a denied gated action and keep the loop paused."""
        receipt = self._record_receipt(
            action,
            status="denied",
            summary="Buddy denied the gated worker request and must replan.",
        )
        report = WorkerReport(
            id=str(uuid4()),
            session_id=action.session_id,
            delegation_id=action.delegation_id,
            worker_agent_id=self.worker.agent_id,
            orchestrator_agent_id=self.orchestrator.agent_id,
            status="needs-approval",
            summary="Lil' Buddy stopped and reported a denied gated step.",
            produced_receipt_ids=(receipt.id,),
            proposed_next_instruction="Buddy should replan without the gated step.",
        )
        self.reports.append(report)
        self.world_state = BuddyWorldState(
            current_mission=self.world_state.current_mission,
            active_surface=_surface_for_action(action.action_type),
            active_tool=None,
            buddy_status="replanning",
            lil_buddy_status="paused",
            visible_artifacts=(f"denied: {action.title}", *self.world_state.visible_artifacts[:11]),
            recent_receipt_ids=(receipt.id, *self.world_state.recent_receipt_ids[:11]),
        )
        return report

    def _record_receipt(
        self,
        action: BuddyAction,
        *,
        status: Literal["completed", "cancelled", "denied"],
        summary: str,
    ) -> BuddyReceipt:
        receipt = BuddyReceipt(
            id=str(uuid4()),
            action_id=action.id,
            session_id=action.session_id,
            delegation_id=action.delegation_id,
            agent_role=action.assigned_agent_role,
            status=status,
            title=action.title,
            summary=summary,
            risk=action.risk,
        )
        self.receipts.append(receipt)
        if self.receipt_writer is not None:
            self.receipt_writer.write(
                ReceiptRecord(
                    action=action.action_type,
                    status="ok" if status == "completed" else "review",
                    summary=summary,
                    metadata={
                        "session_id": receipt.session_id,
                        "delegation_id": receipt.delegation_id,
                        "receipt_id": receipt.id,
                        "risk": receipt.risk,
                        "agent_role": receipt.agent_role,
                    },
                )
            )
        return receipt


def _receipt_summary(action_type: ActionType) -> str:
    summaries: Mapping[ActionType, str] = {
        "browser.summarize": "Lil' Buddy prepared a review-safe page summary draft.",
        "memory.remember": "Lil' Buddy staged a memory write for Buddy review.",
        "note.draft": "Lil' Buddy prepared a note draft.",
        "calendar.draft": "Lil' Buddy prepared a calendar draft without creating an event.",
        "calendar.create": "Lil' Buddy requested calendar creation through Buddy approval.",
    }
    return summaries[action_type]


def _surface_for_action(action_type: ActionType) -> str:
    if action_type.startswith("browser."):
        return "browser"
    if action_type.startswith("memory."):
        return "memory"
    if action_type.startswith("note."):
        return "notes"
    return "calendar"
