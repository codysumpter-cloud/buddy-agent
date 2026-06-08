"""Execution and skill risk policy helpers for Buddy Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Decision = Literal["allow", "deny", "review"]
RiskClass = Literal[
    "read-only",
    "draft-only",
    "write",
    "external-action",
    "destructive",
    "money",
    "identity",
    "location",
    "credential",
    "repo-mutation",
]


@dataclass(frozen=True)
class ExecutionRequest:
    """A requested execution action."""

    command: str
    working_directory: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class ExecutionDecision:
    """Policy decision for an execution request."""

    decision: Decision
    reason: str


class ConservativeExecutionPolicy:
    """Default shell policy for the public alpha."""

    def decide(self, request: ExecutionRequest) -> ExecutionDecision:
        """Review all execution requests by default."""
        return ExecutionDecision(
            decision="review",
            reason=f"Manual review required before running: {request.command}",
        )


@dataclass(frozen=True)
class SkillExecutionRequest:
    """A requested skill execution with declared risk metadata."""

    skill_name: str
    risk_class: str
    auto_executable: bool = False
    requires_explicit_approval: bool = False
    reason: str = ""


@dataclass(frozen=True)
class RiskDecision:
    """Policy decision for a skill execution request."""

    decision: Decision
    reason: str
    risk_class: str


class ConservativeSkillPolicy:
    """Conservative public-alpha policy for skill risk classes."""

    def decide(self, request: SkillExecutionRequest) -> RiskDecision:
        """Decide whether a skill may run, needs review, or is denied."""
        risk_class = request.risk_class.strip().lower()
        if risk_class in {"credential", "money", "destructive", "identity"}:
            return RiskDecision(
                decision="deny",
                reason=f"{risk_class} skills are denied by default in public alpha.",
                risk_class=risk_class,
            )
        if risk_class in {"write", "external-action", "repo-mutation", "location"}:
            return RiskDecision(
                decision="review",
                reason=f"{risk_class} skills require explicit review before execution.",
                risk_class=risk_class,
            )
        if risk_class in {"read-only", "draft-only"}:
            if request.requires_explicit_approval:
                return RiskDecision(
                    decision="review",
                    reason="Skill manifest requires explicit approval.",
                    risk_class=risk_class,
                )
            return RiskDecision(
                decision="allow",
                reason=f"{risk_class} skills are allowed by the default policy.",
                risk_class=risk_class,
            )
        return RiskDecision(
            decision="review",
            reason=f"Unknown risk class requires review: {request.risk_class}",
            risk_class=risk_class,
        )
