"""Callable local model backend contracts for Buddy Agent."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

TextRouteBackend = Callable[[str, Mapping[str, str]], str]


@dataclass
class CallableTextBackend:
    """Small adapter that makes an injected text backend observable in tests.

    This keeps Alpha Runtime Plus honest: a configured local model route can call a
    backend function instead of always falling back to the deterministic echo path.
    """

    name: str
    handler: TextRouteBackend
    prompts: list[str] = field(default_factory=list)

    def generate(self, prompt: str, metadata: Mapping[str, str] | None = None) -> str:
        """Generate a text response from the injected handler."""
        safe_metadata = dict(metadata or {})
        self.prompts.append(prompt)
        return self.handler(prompt, safe_metadata)
