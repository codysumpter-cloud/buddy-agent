"""Omni routing configuration for Buddy Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OmniRouteMode = Literal["off", "hybrid", "direct"]
OmniVisionMode = Literal["local", "hybrid"]


@dataclass(frozen=True)
class OmniConfig:
    """Configuration for Omni-backed routing."""

    enabled: bool = False
    base_url: str = "http://127.0.0.1:8799/api/omni"
    token_env: str = "PRISMBOT_API_TOKEN"
    model: str = "omni-core:phase2"
    route_mode: OmniRouteMode = "hybrid"
    vision_mode: OmniVisionMode = "hybrid"
    timeout_seconds: int = 90
    fallback_to_local: bool = True

    def validate(self) -> None:
        """Validate safe scalar config values."""
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must be an HTTP(S) URL")
