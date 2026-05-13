"""Companion shell contract for loading app-safe Buddy templates."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ..buddy.generate import default_manifest
from ..buddy.render_contract import validate_buddy_manifest


@dataclass
class CompanionShell:
    """Loaded Buddy appearance contract for companion surfaces."""

    manifest: Mapping[str, object]
    source: str = "generated-default"

    @property
    def display_name(self) -> str:
        """Return the display name exposed by the Buddy manifest."""
        value = self.manifest.get("display_name")
        if isinstance(value, str):
            return value
        return "Buddy"

    @classmethod
    def from_default_manifest(cls) -> CompanionShell:
        """Load the built-in default manifest without touching the filesystem."""
        manifest = default_manifest()
        validate_buddy_manifest(manifest)
        return cls(manifest=manifest)

    @classmethod
    def load(cls, path: str | Path) -> CompanionShell:
        """Load and validate a Buddy template manifest from disk."""
        manifest_path = Path(path).expanduser()
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("Buddy manifest must be an object")
        manifest = cast(Mapping[str, object], payload)
        validate_buddy_manifest(manifest)
        return cls(manifest=manifest, source=str(manifest_path))
