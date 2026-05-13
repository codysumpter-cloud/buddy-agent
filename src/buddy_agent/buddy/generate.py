"""Generate app-safe Buddy appearance templates."""

from __future__ import annotations

import json
from pathlib import Path

from .appearance import BUDDY_ANIMATION_STATES, BUDDY_CANVAS_SIZE, default_buddy_template
from .render_contract import validate_buddy_manifest


def default_manifest() -> dict[str, object]:
    """Return the default Buddy generation manifest."""
    template = default_buddy_template()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "template": template.key,
        "display_name": template.display_name,
        "canvas": {"width": BUDDY_CANVAS_SIZE, "height": BUDDY_CANVAS_SIZE},
        "render_modes": list(template.modes),
        "states": list(BUDDY_ANIMATION_STATES),
        "palette": list(template.palette),
        "traits": list(template.traits),
        "customization_options": list(template.customization_options),
        "rules": {
            "buddy_is_pet": True,
            "device_shape_allowed": False,
            "centered": True,
            "equal_padding": True,
            "transparent_background": True,
            "pixel_format": "indexed-color png recommended",
        },
        "assets": {
            "app_icon": "assets/buddy-app-icon.svg",
            "default_pixel": "assets/default-buddy.svg",
            "readme_mascot": "assets/buddy-agent-mascot.svg",
        },
    }
    validate_buddy_manifest(manifest)
    return manifest


def default_ascii_frames() -> dict[str, str]:
    """Return compact ASCII frame placeholders."""
    return {
        "idle": "buddy idle ascii frame",
        "happy": "buddy happy ascii frame",
        "thinking": "buddy thinking ascii frame",
        "sleepy": "buddy sleepy ascii frame",
    }


def write_default_buddy(destination: Path) -> Path:
    """Write a starter Buddy template folder."""
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "buddy.json"
    ascii_path = destination / "ascii_frames.json"
    manifest_path.write_text(json.dumps(default_manifest(), indent=2) + "\n", encoding="utf-8")
    ascii_path.write_text(json.dumps(default_ascii_frames(), indent=2) + "\n", encoding="utf-8")
    return manifest_path
