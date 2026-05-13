"""Configuration loading for Buddy Agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .omni import OmniConfig


def _env_bool(name: str, *, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, *, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class BuddyAgentConfig:
    """Top-level Buddy Agent config."""

    home: Path
    omni: OmniConfig
    enable_gateway: bool = False
    enable_sandbox: bool = False

    @classmethod
    def from_env(cls) -> BuddyAgentConfig:
        """Load config from environment variables."""
        home = Path(os.getenv("BUDDY_HOME", "~/.buddy-agent")).expanduser()
        omni = OmniConfig(
            enabled=_env_bool("BUDDY_OMNI_ENABLED", default=False),
            base_url=os.getenv("BUDDY_OMNI_BASE_URL", "http://127.0.0.1:8799/api/omni"),
            token_env=os.getenv("BUDDY_OMNI_TOKEN_ENV", "PRISMBOT_API_TOKEN"),
            model=os.getenv("BUDDY_OMNI_MODEL", "omni-core:phase2"),
            timeout_seconds=_env_int("BUDDY_OMNI_TIMEOUT_SECONDS", default=90),
            fallback_to_local=_env_bool("BUDDY_OMNI_FALLBACK_TO_LOCAL", default=True),
        )
        omni.validate()
        return cls(
            home=home,
            omni=omni,
            enable_gateway=_env_bool("BUDDY_ENABLE_GATEWAY", default=False),
            enable_sandbox=_env_bool("BUDDY_ENABLE_SANDBOX", default=False),
        )
