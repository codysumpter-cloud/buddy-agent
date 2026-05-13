"""Consent-first permission policy for Buddy companion surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import CompanionCapability

PermissionDecision = Literal["allow", "deny", "ask"]


@dataclass(frozen=True)
class PermissionRequest:
    """A companion capability request."""

    capability: CompanionCapability
    reason: str
    user_initiated: bool = False


@dataclass(frozen=True)
class PermissionResult:
    """Result of a permission policy check."""

    decision: PermissionDecision
    reason: str


class CompanionPermissionPolicy:
    """Default consent-first policy for companion surfaces."""

    always_allowed: tuple[CompanionCapability, ...] = ("overlay", "chat", "widget")
    ask_first: tuple[CompanionCapability, ...] = (
        "voice",
        "context_bridge",
        "shortcut",
        "approved_action",
    )

    def decide(self, request: PermissionRequest) -> PermissionResult:
        """Return a safe default permission decision."""
        if request.capability in self.always_allowed and request.user_initiated:
            return PermissionResult(decision="allow", reason="User-initiated companion UI action")
        if request.capability in self.ask_first:
            return PermissionResult(decision="ask", reason="User consent required")
        return PermissionResult(decision="deny", reason="Capability is not recognized")
