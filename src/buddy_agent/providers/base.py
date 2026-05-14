"""Provider contracts for Buddy Agent runtime responses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ProviderRequest:
    """Input sent from the runtime shell to a provider."""

    content: str
    session_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResponse:
    """Response returned by a provider."""

    content: str
    provider: str
    model: str = "local"
    metadata: Mapping[str, str] = field(default_factory=dict)


class BaseProvider(Protocol):
    """Protocol implemented by runtime providers."""

    @property
    def name(self) -> str:
        """Stable provider name."""
        ...

    def respond(self, request: ProviderRequest) -> ProviderResponse:
        """Return a provider response for a runtime request."""
        ...
