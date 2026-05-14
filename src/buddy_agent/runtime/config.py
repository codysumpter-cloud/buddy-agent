"""Runtime configuration for Buddy Agent.

The Alpha Runtime Plus milestone keeps configuration local and explicit. The loader
accepts JSON so later Hermes/Buddy config formats can be mapped into this native
shape without coupling the runtime to upstream file layouts.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

DEFAULT_RUNTIME_CONFIG_ENV = "BUDDY_RUNTIME_CONFIG"
DEFAULT_TEMPLATE_PATH = Path("templates/default-buddy/buddy.json")
DEFAULT_SYSTEM_PROMPT = (
    "You are Buddy, a permission-gated Prismtek companion runtime. "
    "Use local memory and retrieval context when available."
)


@dataclass(frozen=True)
class RuntimeConfig:
    """Buddy-native runtime configuration."""

    name: str = "buddy-alpha-plus"
    backend: str = "local-template"
    model: str = "buddy-local"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    memory_limit: int = 5
    template_path: Path = DEFAULT_TEMPLATE_PATH
    restricted_integrations_enabled: bool = False

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RuntimeConfig:
        """Build a config object from a JSON-like mapping."""
        template_path = payload.get("template_path", DEFAULT_TEMPLATE_PATH)
        memory_limit = payload.get("memory_limit", 5)
        return cls(
            name=str(payload.get("name", "buddy-alpha-plus")),
            backend=str(payload.get("backend", "local-template")),
            model=str(payload.get("model", "buddy-local")),
            system_prompt=str(payload.get("system_prompt", DEFAULT_SYSTEM_PROMPT)),
            memory_limit=int(memory_limit),
            template_path=Path(str(template_path)),
            restricted_integrations_enabled=bool(
                payload.get("restricted_integrations_enabled", False)
            ),
        )

    def metadata(self) -> dict[str, str]:
        """Return string metadata safe to pass through runtime adapters."""
        return {
            "runtime": self.name,
            "backend": self.backend,
            "model": self.model,
            "restricted_integrations_enabled": str(self.restricted_integrations_enabled).lower(),
        }


def load_runtime_config(path: str | Path | None = None) -> RuntimeConfig:
    """Load runtime config from JSON, falling back to safe local defaults."""
    config_path: Path | None
    if path is not None:
        config_path = Path(path).expanduser()
    else:
        configured = os.getenv(DEFAULT_RUNTIME_CONFIG_ENV)
        config_path = Path(configured).expanduser() if configured else None

    if config_path is None or not config_path.exists():
        return RuntimeConfig()

    raw_payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw_payload, Mapping):
        raise ValueError("Buddy runtime config must be a JSON object")
    return RuntimeConfig.from_mapping(cast(Mapping[str, Any], raw_payload))
