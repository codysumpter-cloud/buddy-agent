"""Local text backend for Buddy Agent."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from .types import RuntimeMessage


@dataclass(frozen=True)
class RuntimeBackendResponse:
    """Response returned by a runtime backend."""

    content: str
    metadata: Mapping[str, str] = field(default_factory=dict)


class RuntimeBackend(Protocol):
    """Boundary for runtime text response implementations."""

    def respond(
        self,
        text: str,
        *,
        messages: Sequence[RuntimeMessage],
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> RuntimeBackendResponse:
        """Return a response for the active runtime turn."""
        ...


@dataclass(frozen=True)
class LocalTemplateBackend:
    """Deterministic local backend for Alpha Runtime Plus."""

    name: str = "local-template"

    def respond(
        self,
        text: str,
        *,
        messages: Sequence[RuntimeMessage],
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> RuntimeBackendResponse:
        """Return a deterministic local response."""
        runtime_metadata = dict(metadata or {})
        runtime_name = runtime_metadata.get("runtime", "buddy-alpha-plus")
        context_items = tuple(item.strip() for item in context if item.strip())
        context_line = ""
        if context_items:
            context_line = " Context: " + " | ".join(context_items)
        content = (
            f"Buddy runtime [{runtime_name}] processed: {text.strip()}"
            f"{context_line}"
            f" (turns={len(messages)})"
        )
        return RuntimeBackendResponse(
            content=content,
            metadata={"backend": self.name, "runtime": runtime_name, "turns": str(len(messages))},
        )
