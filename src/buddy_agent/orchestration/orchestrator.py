"""Buddy orchestrator scaffold for the default Buddy + Lil' Buddy loop."""

from __future__ import annotations

from dataclasses import dataclass, field

from .envelopes import (
    OrchestrationTrace,
    ReviewEnvelope,
    SafetyClass,
    TaskEnvelope,
    ToolContract,
)
from .worker import LilBuddyWorker

HIGH_RISK_TERMS = (
    "account",
    "buy",
    "calendar",
    "camera",
    "credential",
    "delete",
    "device",
    "email",
    "key",
    "money",
    "password",
    "post",
    "purchase",
    "send",
    "token",
    "wallet",
)
MEDIUM_RISK_TERMS = (
    "branch",
    "commit",
    "file",
    "repo",
    "run",
    "schema",
    "test",
    "write",
)

SYSTEM_PROMPT_TEMPLATE = (
    "For every task, instantiate Buddy as orchestrator and at least one Lil' Buddy as worker.\n"
    "Buddy must preserve the user's intent, create a short plan, delegate scoped work, "
    "review the result, apply safety/policy checks, and only then respond.\n"
    "Lil' Buddy must execute only the delegated scope and return structured results.\n"
    "Use knowledge-vault for durable knowledge, buddy-brain for governance, "
    "buddy-agent for runtime execution, and omni-buddy for local embodied/device integrations."
)


@dataclass(frozen=True)
class BuddyOrchestrator:
    """Small local orchestrator that delegates one task to one Lil' Buddy."""

    worker: LilBuddyWorker = field(default_factory=LilBuddyWorker)
    name: str = "Buddy"

    def run(self, user_intent: str) -> dict[str, object]:
        """Run the local demo loop and return a structured trace."""
        intent = user_intent.strip() or "Show the Buddy + Lil' Buddy default loop."
        plan = self.plan(intent)
        task = self.delegate(intent)
        result = self.worker.execute(task)
        review = self.review(task, result_findings=result.findings, result_risks=result.risks)
        final_response = self.respond(intent, review)
        trace = OrchestrationTrace(
            user_intent=intent,
            buddy_plan=plan,
            task=task,
            result=result,
            review=review,
            final_response=final_response,
            durable_memory_targets=(
                "knowledge-vault/99-System/Buddy Standards/",
                "buddy-brain/config/runtime/buddy-lil-buddy-contract.json",
            ),
        )
        payload = trace.to_dict()
        payload["system_prompt_template"] = SYSTEM_PROMPT_TEMPLATE
        return payload

    def plan(self, user_intent: str) -> tuple[str, ...]:
        """Create Buddy's short plan for the local loop."""
        return (
            "Preserve the human intent and classify risk.",
            "Delegate one scoped local reasoning task to Lil' Buddy.",
            "Review the structured result against scope, evidence, and safety gates.",
            "Respond only after Buddy Review.",
        )

    def delegate(self, user_intent: str) -> TaskEnvelope:
        """Create the task envelope for Lil' Buddy."""
        safety_class = classify_safety(user_intent)
        return TaskEnvelope.build(
            user_intent=user_intent,
            delegated_scope=(
                "Summarize the intent, confirm the Buddy/Lil' Buddy route, and identify "
                "whether Buddy must escalate before action."
            ),
            constraints=(
                "No network calls.",
                "No external secrets.",
                "No repo mutation.",
                "Return structured results only.",
                "Buddy owns the final response.",
            ),
            approved_tools=(
                ToolContract(
                    name="local_reasoning",
                    contract="draft-only",
                    description="Local deterministic reasoning for demo output.",
                ),
            ),
            safety_class=safety_class,
            orchestrator=self.name,
            worker=self.worker.name,
        )

    def review(
        self,
        task: TaskEnvelope,
        *,
        result_findings: tuple[str, ...],
        result_risks: tuple[str, ...],
    ) -> ReviewEnvelope:
        """Review Lil' Buddy output before Buddy responds."""
        if task.safety_class == "blocked":
            return ReviewEnvelope(
                task_id=task.task_id,
                reviewer=self.name,
                status="block",
                approved_findings=(),
                notes=("Blocked safety class requires Buddy to stop before action.",),
                escalation_required=True,
            )
        if task.safety_class == "high" or result_risks:
            return ReviewEnvelope(
                task_id=task.task_id,
                reviewer=self.name,
                status="escalate",
                approved_findings=result_findings,
                notes=("High-risk or gated work requires explicit Buddy/human approval.",),
                escalation_required=True,
            )
        return ReviewEnvelope(
            task_id=task.task_id,
            reviewer=self.name,
            status="approved",
            approved_findings=result_findings,
            notes=("Local demo used draft-only tooling and produced no external action.",),
            escalation_required=False,
        )

    def respond(self, user_intent: str, review: ReviewEnvelope) -> str:
        """Create Buddy's final human-facing response after review."""
        if review.status == "block":
            return "Buddy reviewed Lil' Buddy's result and blocked the task before action."
        if review.escalation_required:
            return (
                "Buddy reviewed Lil' Buddy's result and would pause for approval before any "
                f"gated action for: {user_intent}"
            )
        return (
            "Buddy reviewed Lil' Buddy's structured result and approved the local demo response "
            f"for: {user_intent}"
        )


def classify_safety(user_intent: str) -> SafetyClass:
    """Classify task safety for the local scaffold."""
    lowered = user_intent.lower()
    if "bypass safety" in lowered or "ignore review" in lowered:
        return "blocked"
    if any(term in lowered for term in HIGH_RISK_TERMS):
        return "high"
    if any(term in lowered for term in MEDIUM_RISK_TERMS):
        return "medium"
    return "low"
