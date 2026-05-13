"""Shared contracts for companion surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

CompanionState = Literal[
    "idle",
    "listening",
    "thinking",
    "watching",
    "acting",
    "happy",
    "sleepy",
    "needs_attention",
]

CompanionCapability = Literal[
    "overlay",
    "chat",
    "voice",
    "context_bridge",
    "widget",
    "shortcut",
    "approved_action",
]


@dataclass(frozen=True)
class CompanionEvent:
    """Event emitted by a Buddy companion surface."""

    name: str
    state: CompanionState
    capability: CompanionCapability
    metadata: dict[str, str] = field(default_factory=dict)
