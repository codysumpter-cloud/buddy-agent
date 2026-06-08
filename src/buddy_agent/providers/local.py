"""Local provider implementations."""

from __future__ import annotations

from dataclasses import dataclass

from .base import ProviderRequest, ProviderResponse


@dataclass(frozen=True)
class LocalEchoProvider:
    """Offline-safe deterministic provider used by default."""

    prefix: str = "Buddy local echo"

    @property
    def name(self) -> str:
        """Stable provider name."""
        return "local"

    def respond(self, request: ProviderRequest) -> ProviderResponse:
        """Return a deterministic local response without network access."""
        content = request.content.strip() or "(empty message)"
        return ProviderResponse(
            content=f"{self.prefix}: {content}",
            provider=self.name,
            model="local-echo",
            metadata={"network": "disabled"},
        )
