"""Execution policy helpers for Buddy Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Decision = Literal["allow", "deny", "review"]


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
    """Default policy for the scaffold.

    The policy sends every command to review until a stricter allowlist is implemented.
    """

    def decide(self, request: ExecutionRequest) -> ExecutionDecision:
        """Review all execution requests by default."""
        return ExecutionDecision(
            decision="review",
            reason=f"Manual review required before running: {request.command}",
        )
