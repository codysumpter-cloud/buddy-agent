"""Minimal Buddy Agent runtime engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from buddy_agent.providers import BaseProvider, ProviderRequest, create_provider_from_env
from buddy_agent.receipts import ReceiptRecord, ReceiptWriter

from .tools import ToolRegistry
from .types import RuntimeState, ToolCall, ToolResult


@dataclass
class RuntimeEngine:
    """A small runtime engine that can be expanded with Hermes-derived behavior."""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    provider: BaseProvider = field(default_factory=create_provider_from_env)
    receipt_writer: ReceiptWriter | None = None
    state: RuntimeState = field(init=False)

    def __post_init__(self) -> None:
        self.state = RuntimeState(session_id=self.session_id)

    def receive(self, content: str) -> str:
        """Record a user message and return a provider response."""
        self.state.append_message("user", content)
        provider_response = self.provider.respond(
            ProviderRequest(content=content, session_id=self.session_id)
        )
        response = provider_response.content
        self.state.append_message("assistant", response)
        if self.receipt_writer is not None:
            self.receipt_writer.write(
                ReceiptRecord(
                    action="runtime.receive",
                    status="ok",
                    summary="Provider response emitted without recording prompt content.",
                    metadata={
                        "provider": provider_response.provider,
                        "model": provider_response.model,
                        "input_length": len(content),
                    },
                )
            )
        return response

    def call_tool(self, name: str, **arguments: object) -> ToolResult:
        """Call a registered tool and record the result."""
        result = self.tools.call(ToolCall(name=name, arguments=arguments))
        self.state.tool_results.append(result)
        return result
