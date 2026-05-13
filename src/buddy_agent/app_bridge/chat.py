"""Chat route contracts for app surfaces talking to Buddy Agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ibe_more import IBeMoreSurface


@dataclass(frozen=True)
class BuddyAppChatRequest:
    """A chat request from an approved app-native Buddy surface."""

    buddy_id: str
    prompt: str
    surface: IBeMoreSurface = "chat"
    payload: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class BuddyAppChatResponse:
    """A response suitable for app-native Buddy chat surfaces."""

    ok: bool
    buddy_id: str
    message: str
    detail: str = ""
    payload: dict[str, str] = field(default_factory=dict)
