"""Typed adapter contracts for integrating Buddy Agent with related systems.

These protocols keep imports one-way and prevent runtime code from depending directly on
product UI, local hardware code, or vault storage implementations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class AdapterHealth:
    """Health status returned by an integration adapter."""

    name: str
    ok: bool
    detail: str = ""


@dataclass(frozen=True)
class RetrievedSource:
    """A source returned by a retrieval provider."""

    source_id: str
    title: str
    text: str
    metadata: Mapping[str, str]


@runtime_checkable
class BuddyBrainAdapter(Protocol):
    """Boundary for operator policy, runbooks, skills, and council context."""

    def health(self) -> AdapterHealth:
        """Return adapter health without mutating external state."""
        ...

    def load_startup_context(self) -> Mapping[str, str]:
        """Load startup context documents needed by the runtime."""
        ...


@runtime_checkable
class OmniBuddyAdapter(Protocol):
    """Boundary for local/offline, voice/vision, and Omni-backed runtime behavior."""

    def health(self) -> AdapterHealth:
        """Return adapter health without mutating external state."""
        ...

    def route_text(self, prompt: str, *, metadata: Mapping[str, str] | None = None) -> str:
        """Route a text prompt through the configured Omni/local backend."""
        ...


@runtime_checkable
class PrismtekAppBridge(Protocol):
    """Boundary for app-facing Buddy lifecycle and relay contracts."""

    def health(self) -> AdapterHealth:
        """Return adapter health without mutating external state."""
        ...

    def publish_event(self, event_name: str, payload: Mapping[str, object]) -> None:
        """Publish a sanitized app-facing event."""
        ...


@runtime_checkable
class KnowledgeVaultProvider(Protocol):
    """Boundary for retrieval and source provenance backed by Knowledge Vault."""

    def health(self) -> AdapterHealth:
        """Return adapter health without mutating external state."""
        ...

    def search(self, query: str, *, limit: int = 5) -> Sequence[RetrievedSource]:
        """Search the vault and return provenance-preserving sources."""
        ...
