"""Minimal Buddy Agent runtime engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .tools import ToolRegistry
from .types import RuntimeState, ToolCall, ToolResult


@dataclass
class RuntimeEngine:
    """A small runtime engine that can be expanded with Hermes-derived behavior."""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    tools: ToolRegistry = field(default_factory=ToolRegistry)

    def __post_init__(self) -> None:
        self.state = RuntimeState(session_id=self.session_id)

    def receive(self, content: str) -> str:
        """Record a user message and return a scaffold response."""
        self.state.append_message("user", content)
        response = "Buddy Agent runtime scaffold received your message."
        self.state.append_message("assistant", response)
        return response

    def call_tool(self, name: str, **arguments: object) -> ToolResult:
        """Call a registered tool and record the result."""
        result = self.tools.call(ToolCall(name=name, arguments=arguments))
        self.state.tool_results.append(result)
        return result
