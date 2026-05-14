"""Receipt record primitives."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | dict[str, "JSONValue"] | list["JSONValue"]
ReceiptStatus: TypeAlias = Literal["ok", "error", "review", "deny"]


@dataclass(frozen=True)
class ReceiptRecord:
    """Serializable local receipt record."""

    action: str
    status: ReceiptStatus
    summary: str
    metadata: Mapping[str, JSONValue] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, JSONValue]:
        """Return a JSON-serializable dictionary."""
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "status": self.status,
            "summary": self.summary,
            "metadata": dict(self.metadata),
        }
