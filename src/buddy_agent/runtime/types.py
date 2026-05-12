"""Core runtime value types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeMessage:
    """A message exchanged with the runtime."""

    role: str
    content: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCall:
    """A structured tool call request."""

    name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    """A structured tool call result."""

    name: str
    ok: bool
    content: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass
class RuntimeState:
    """Minimal runtime state for the scaffold agent."""

    session_id: str
    messages: list[RuntimeMessage] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)

    def append_message(self, role: str, content: str) -> RuntimeMessage:
        """Append a message to the active session."""
        message = RuntimeMessage(role=role, content=content)
        self.messages.append(message)
        return message
