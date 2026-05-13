"""Companion shell contracts for floating Buddy and iBeMore surfaces."""

from .contracts import CompanionCapability, CompanionEvent, CompanionState
from .permissions import (
    CompanionPermissionPolicy,
    PermissionDecision,
    PermissionRequest,
    PermissionResult,
)

__all__ = [
    "CompanionCapability",
    "CompanionEvent",
    "CompanionPermissionPolicy",
    "CompanionState",
    "PermissionDecision",
    "PermissionRequest",
    "PermissionResult",
]
