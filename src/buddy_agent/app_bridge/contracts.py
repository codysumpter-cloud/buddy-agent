"""Contracts shared with Prismtek app surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, cast

BuddyEventName = Literal[
    "buddy.created",
    "buddy.updated",
    "buddy.trained",
    "buddy.care_changed",
    "buddy.trade_exported",
]

BUDDY_EVENT_NAMES: tuple[BuddyEventName, ...] = (
    "buddy.created",
    "buddy.updated",
    "buddy.trained",
    "buddy.care_changed",
    "buddy.trade_exported",
)


def normalize_buddy_event_name(value: str) -> BuddyEventName:
    """Return a supported Buddy event name, falling back to a safe update event."""
    if value in BUDDY_EVENT_NAMES:
        return cast(BuddyEventName, value)
    return "buddy.updated"


@dataclass(frozen=True)
class BuddyEvent:
    """A sanitized event that can be sent to an app surface."""

    name: BuddyEventName
    buddy_id: str
    body: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TradePackageSummary:
    """Summary metadata for a Buddy trade package."""

    package_id: str
    buddy_id: str
    display_name: str
    checksum: str
