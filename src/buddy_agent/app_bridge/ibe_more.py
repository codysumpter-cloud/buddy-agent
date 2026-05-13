"""iBeMore app bridge contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

IBeMoreSurface = Literal["home", "chat", "voice", "widget", "shortcut", "training", "care"]
IBeMoreAction = Literal[
    "open_chat",
    "start_voice",
    "stop_voice",
    "show_buddy",
    "train_buddy",
    "care_action",
    "sync_appearance",
]


@dataclass(frozen=True)
class IBeMoreRequest:
    """Request sent from an iBeMore surface to Buddy Agent."""

    surface: IBeMoreSurface
    action: IBeMoreAction
    buddy_id: str
    payload: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class IBeMoreResponse:
    """Response sent from Buddy Agent back to an iBeMore surface."""

    ok: bool
    message: str
    buddy_id: str
    payload: dict[str, str] = field(default_factory=dict)


def acknowledge_request(request: IBeMoreRequest, message: str = "accepted") -> IBeMoreResponse:
    """Create a simple successful response for app bridge tests and local flows."""
    return IBeMoreResponse(ok=True, message=message, buddy_id=request.buddy_id)
