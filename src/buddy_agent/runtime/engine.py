"""Buddy Agent runtime engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from uuid import uuid4

from .backends import LocalTemplateBackend, ModelBackend, ModelResponse
from .config import RuntimeConfig, load_runtime_config
from .tools import ToolRegistry
from .types import RuntimeState, ToolCall, ToolResult


@dataclass
class RuntimeEngine:
    """Runtime engine with a callable model backend boundary.

    This is the first Buddy-native reimplementation seam for Hermes-style runtime
    orchestration: state is recorded, config is loaded, tools stay structured, and
    text generation goes through an explicit backend adapter instead of inline echo
    behavior.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    config: RuntimeConfig = field(default_factory=load_runtime_config)
    backend: ModelBackend = field(default_factory=LocalTemplateBackend)
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
        """Record a user message and return a backend-generated response."""
        self.state.append_message("user", content)
        response = self.generate(content, metadata=metadata, context=context)
        self.state.append_message("assistant", response.content)
        return response.content

    def generate(
        self,
        content: str,
        *,
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> ModelResponse:
        """Generate a response through the configured backend."""
        runtime_metadata = self.config.metadata()
        if metadata:
            runtime_metadata.update(metadata)
        return self.backend.generate(
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
