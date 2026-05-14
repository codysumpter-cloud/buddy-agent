"""Companion shell contracts for floating Buddy and iBeMore surfaces."""

from .contracts import CompanionCapability, CompanionEvent, CompanionState
from .permissions import (
    CompanionPermissionPolicy,
    PermissionDecision,
    PermissionRequest,
    PermissionResult,
)
from .shell import CompanionShell, load_companion_shell

__all__ = [
    "CompanionCapability",
    "CompanionEvent",
    "CompanionPermissionPolicy",
    "CompanionShell",
    "CompanionState",
    "PermissionDecision",
    "PermissionRequest",
    "PermissionResult",
    "load_companion_shell",
]
