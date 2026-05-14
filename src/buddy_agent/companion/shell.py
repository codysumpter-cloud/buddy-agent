"""Companion shell loader for app-facing Buddy templates."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from buddy_agent.buddy.render_contract import validate_buddy_manifest
from buddy_agent.runtime.config import DEFAULT_TEMPLATE_PATH

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class CompanionShell:
    """Loaded companion shell contract for Buddy app surfaces."""

    buddy_id: str
    display_name: str
    manifest: Mapping[str, object]
    template_path: Path = DEFAULT_TEMPLATE_PATH
    surfaces: tuple[str, ...] = ("desktop", "widget", "ibe_more")
    permissions_required: tuple[str, ...] = ("chat", "widget", "context_bridge", "shortcut")
    metadata: Mapping[str, str] = field(default_factory=dict)

    def state_names(self) -> tuple[str, ...]:
        """Return app-renderable animation state names."""
        states = self.manifest.get("states", ())
        if not isinstance(states, list):
            return ()
        return tuple(str(state) for state in states)


def resolve_template_path(template_path: str | Path = DEFAULT_TEMPLATE_PATH) -> Path:
    """Resolve template paths independently of the caller's current directory."""
    path = Path(template_path).expanduser()
    if path.is_absolute() or path.exists():
        return path

    repo_relative = PROJECT_ROOT / path
    if repo_relative.exists():
        return repo_relative

    return path


def load_companion_shell(template_path: str | Path = DEFAULT_TEMPLATE_PATH) -> CompanionShell:
    """Load and validate a Buddy template for companion app surfaces."""
    path = resolve_template_path(template_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Buddy companion template must be a JSON object")
    manifest = cast(Mapping[str, object], payload)
    validate_buddy_manifest(manifest)
    return CompanionShell(
        buddy_id=str(manifest.get("template", "default-buddy")),
        display_name=str(manifest.get("display_name", "Default Buddy")),
        manifest=manifest,
        template_path=path,
        metadata={"template": str(path)},
    )
