"""Gateway contracts for normalized chat surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Contact:
    """A normalized sender identity."""

    platform: str
    user_id: str
    display_name: str | None = None


@dataclass(frozen=True)
class InboundMessage:
    """A normalized inbound message."""

    contact: Contact
    text: str
    channel_id: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OutboundMessage:
    """A normalized outbound message."""

    text: str
    channel_id: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)
