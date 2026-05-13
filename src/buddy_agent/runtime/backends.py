"""Callable model backend contracts for Buddy Agent."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .types import RuntimeMessage


@dataclass(frozen=True)
class ModelResponse:
    """A response returned by a model backend."""

    content: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@runtime_checkable
class ModelBackend(Protocol):
    """Boundary for local, offline, or remote model backends."""

    def generate(
        self,
        prompt: str,
        *,
        messages: Sequence[RuntimeMessage],
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> ModelResponse:
        """Generate a response for the active runtime turn."""
        ...


@dataclass(frozen=True)
class LocalTemplateBackend:
    """Deterministic local backend used before model-provider credentials exist.

    This is intentionally a real callable backend boundary rather than inline echo
    routing. It consumes runtime metadata, history, and retrieval context so tests can
    exercise the same path a later llama.cpp, MLX, Ollama, or hosted adapter will use.
    """

    name: str = "local-template"

    def generate(
        self,
        prompt: str,
        *,
        messages: Sequence[RuntimeMessage],
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> ModelResponse:
        """Generate a deterministic local response."""
        runtime_metadata = dict(metadata or {})
        model = runtime_metadata.get("model", "buddy-local")
        context_line = ""
        if context:
            context_line = " Context: " + " | ".join(item.strip() for item in context if item.strip())
        history_count = len(messages)
        content = (
            f"Buddy runtime [{model}] processed: {prompt.strip()}"
            f"{context_line}"
            f" (turns={history_count})"
        )
        return ModelResponse(
            content=content,
            metadata={"backend": self.name, "model": model, "turns": str(history_count)},
        )
