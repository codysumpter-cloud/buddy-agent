"""Configuration loading for Buddy Agent."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from .omni import OmniConfig


def _as_bool(value: object, *, default: bool) -> bool:
    """Coerce a config value into a boolean."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    raise ValueError(f"Expected boolean-like value, got {type(value).__name__}")


def _as_int(value: object, *, default: int) -> int:
    """Coerce a config value into an integer."""
    if value is None:
        return default
    if isinstance(value, bool):
        raise ValueError("Expected integer value, got bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"Expected integer-like value, got {type(value).__name__}")


def _as_mapping(value: object, *, name: str) -> Mapping[str, object]:
    """Return a mapping value or raise a useful config error."""
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise ValueError(f"{name} must be an object")


def _as_optional_path(value: object) -> Path | None:
    """Return an optional expanded path from config data."""
    if value is None or value == "":
        return None
    return Path(str(value)).expanduser()


def _as_path_tuple(value: object) -> tuple[Path, ...]:
    """Return a stable tuple of expanded source paths."""
    if value is None or value == "":
        return ()
    if isinstance(value, str):
        parts = [part for part in value.split(os.pathsep) if part]
        return tuple(Path(part).expanduser() for part in parts)
    if isinstance(value, Sequence) and not isinstance(value, bytes):
        return tuple(Path(str(part)).expanduser() for part in value)
    raise ValueError("knowledge_paths must be a string or list")


def _env_bool(name: str, *, default: bool) -> bool:
    return _as_bool(os.getenv(name), default=default)


def _env_int(name: str, *, default: int) -> int:
    return _as_int(os.getenv(name), default=default)


@dataclass(frozen=True)
class BuddyAgentConfig:
    """Top-level Buddy Agent config.

    Defaults are intentionally local-first and safety-gated. Restricted integrations stay
    disabled unless a future policy layer explicitly enables them with tests and docs.
    """

    home: Path
    omni: OmniConfig
    enable_gateway: bool = False
    enable_sandbox: bool = False
    memory_path: Path | None = None
    retrieval_enabled: bool = True
    knowledge_paths: tuple[Path, ...] = ()
    operator_profile: str = "buddy-alpha-plus"
    restricted_integrations_enabled: bool = False

    @property
    def resolved_memory_path(self) -> Path:
        """Return the memory path used by configured runtime entrypoints."""
        return self.memory_path or self.home / "memory.json"

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> BuddyAgentConfig:
        """Load config from a parsed JSON-compatible mapping."""
        home = Path(str(mapping.get("home", "~/.buddy-agent"))).expanduser()
        omni_data = _as_mapping(mapping.get("omni"), name="omni")
        omni = OmniConfig(
            enabled=_as_bool(omni_data.get("enabled"), default=False),
            base_url=str(omni_data.get("base_url", "http://127.0.0.1:8799/api/omni")),
            token_env=str(omni_data.get("token_env", "PRISMBOT_API_TOKEN")),
            model=str(omni_data.get("model", "omni-core:phase2")),
            timeout_seconds=_as_int(omni_data.get("timeout_seconds"), default=90),
            fallback_to_local=_as_bool(omni_data.get("fallback_to_local"), default=True),
        )
        omni.validate()
        return cls(
            home=home,
            omni=omni,
            enable_gateway=_as_bool(mapping.get("enable_gateway"), default=False),
            enable_sandbox=_as_bool(mapping.get("enable_sandbox"), default=False),
            memory_path=_as_optional_path(mapping.get("memory_path")),
            retrieval_enabled=_as_bool(mapping.get("retrieval_enabled"), default=True),
            knowledge_paths=_as_path_tuple(mapping.get("knowledge_paths")),
            operator_profile=str(mapping.get("operator_profile", "buddy-alpha-plus")),
            restricted_integrations_enabled=_as_bool(
                mapping.get("restricted_integrations_enabled"), default=False
            ),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> BuddyAgentConfig:
        """Load runtime config from a JSON file."""
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        return cls.from_mapping(_as_mapping(payload, name="config"))

    @classmethod
    def from_env(cls) -> BuddyAgentConfig:
        """Load config from environment variables."""
        home = Path(os.getenv("BUDDY_HOME", "~/.buddy-agent")).expanduser()
        memory_path = Path(os.getenv("BUDDY_MEMORY_FILE", "~/.buddy_agent/memory.json")).expanduser()
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
            memory_path=memory_path,
            retrieval_enabled=_env_bool("BUDDY_RETRIEVAL_ENABLED", default=True),
            knowledge_paths=_as_path_tuple(os.getenv("BUDDY_KNOWLEDGE_PATHS")),
            operator_profile=os.getenv("BUDDY_OPERATOR_PROFILE", "buddy-alpha-plus"),
            restricted_integrations_enabled=_env_bool(
                "BUDDY_RESTRICTED_INTEGRATIONS_ENABLED", default=False
            ),
        )
