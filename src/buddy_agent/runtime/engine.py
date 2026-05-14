"""Buddy Agent runtime engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from uuid import uuid4

from .backends import LocalTemplateBackend, RuntimeBackend, RuntimeBackendResponse
from .config import RuntimeConfig, load_runtime_config
from .tools import ToolRegistry
from .types import RuntimeState, ToolCall, ToolResult


@dataclass
class RuntimeEngine:
    """Runtime engine with config, state, tools, and a backend boundary."""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    config: RuntimeConfig = field(default_factory=load_runtime_config)
    backend: RuntimeBackend = field(default_factory=LocalTemplateBackend)
    state: RuntimeState = field(init=False)

    def __post_init__(self) -> None:
        self.state = RuntimeState(session_id=self.session_id)

    def receive(
        self,
        content: str,
        *,
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> str:
        """Record a user message and return a backend response."""
        self.state.append_message("user", content)
        response = self.respond(content, metadata=metadata, context=context)
        self.state.append_message("assistant", response.content)
        return response.content

    def respond(
        self,
        content: str,
        *,
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> RuntimeBackendResponse:
        """Route one turn through the configured backend."""
        runtime_metadata = self.config.metadata()
        if metadata:
            runtime_metadata.update(metadata)
        return self.backend.respond(
            content,
            messages=self.state.messages,
            metadata=runtime_metadata,
            context=context,
        )

    def call_tool(self, name: str, **arguments: object) -> ToolResult:
        """Call a registered tool and record the result."""
        result = self.tools.call(ToolCall(name=name, arguments=arguments))
        self.state.tool_results.append(result)
        return result
