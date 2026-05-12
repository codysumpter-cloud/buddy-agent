"""Tool registry primitives for Buddy Agent."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .types import ToolCall, ToolResult

ToolHandler = Callable[[Mapping[str, Any]], ToolResult]


@dataclass(frozen=True)
class ToolDefinition:
    """Metadata and handler for a runtime tool."""

    name: str
    description: str
    handler: ToolHandler


class ToolRegistry:
    """Small deterministic tool registry used by the scaffold runtime."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        """Register a tool definition.

        Raises:
            ValueError: if another tool already uses the same name.
        """
        if definition.name in self._tools:
            raise ValueError(f"Tool already registered: {definition.name}")
        self._tools[definition.name] = definition

    def names(self) -> tuple[str, ...]:
        """Return registered tool names in stable order."""
        return tuple(sorted(self._tools))

    def call(self, call: ToolCall) -> ToolResult:
        """Execute a registered tool call."""
        definition = self._tools.get(call.name)
        if definition is None:
            return ToolResult(name=call.name, ok=False, content=f"Unknown tool: {call.name}")
        return definition.handler(call.arguments)
