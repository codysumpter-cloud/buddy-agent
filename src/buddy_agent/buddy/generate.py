"""Generate app-safe Buddy appearance templates."""

from __future__ import annotations

import json
from pathlib import Path

from .appearance import BUDDY_ANIMATION_STATES, BUDDY_CANVAS_SIZE, default_buddy_template
from .render_contract import validate_buddy_manifest


def default_animation_cycle() -> dict[str, object]:
    """Return the default Buddy state cycle used by ASCII and pixel renderers."""
    return {
        "states": list(BUDDY_ANIMATION_STATES),
        "frame_duration_ms": 900,
        "loop": True,
    }


def default_style_reference() -> dict[str, object]:
    """Return the canonical default Buddy art direction."""
    return {
        "body": "round mint/cyan pixel-pet body",
        "outline": "deep navy high-contrast pixel outline",
        "face": "large soft face panel with dot eyes, small smile, and plus/blush cheeks",
        "ears": "heart-shaped antler ears",
        "details": [
            "small top tuft",
            "tiny side arms",
            "tiny rounded feet",
            "gold heart belly charm",
            "asymmetric pixel highlights",
        ],
        "must_not": [
            "screen body",
            "phone body",
            "gamepad body",
            "blurred painterly rendering",
            "3D mascot rendering",
        ],
    }


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
        "animation": default_animation_cycle(),
        "palette": list(template.palette),
        "traits": list(template.traits),
        "customization_options": list(template.customization_options),
        "style_reference": default_style_reference(),
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


def _ascii_frame(lines: tuple[str, ...]) -> str:
    return "\n".join(lines)


def default_ascii_frames() -> dict[str, str]:
    """Return compact ASCII frames that visibly cycle through Buddy states."""
    return {
        "idle": _ascii_frame(
            (
                "     <3           <3     ",
                "   .'  '.       .'  '.   ",
                "  /  ..  \\_^_/  ..  \\  ",
                "       .-#####-.       ",
                "   o  /# .---. #\\  o   ",
                "     |# | o o | #|      ",
                "     |# |  u  | #|      ",
                "      \\#'---'#/       ",
                "        ##<3##         ",
                "        ##  ##         ",
            )
        ),
        "happy": _ascii_frame(
            (
                "   \\<3/       \\<3/   ",
                "   .'  '.     .'  '.   ",
                "  /  **  \\_^_/  **  \\ ",
                "       .-#####-.       ",
                "  \\o /# .---. #\\ o/  ",
                "     |# | ^ ^ | #|      ",
                "     |# | \\_/ | #|     ",
                "      \\#'---'#/       ",
                "       *##<3##*        ",
                "        ##  ##         ",
            )
        ),
        "thinking": _ascii_frame(
            (
                "     <3           <3  ? ",
                "   .'  '.       .'  '.  ",
                "  /  ..  \\_^_/  ..  \\ ",
                "       .-#####-.    ?  ",
                "   o  /# .---. #\\     ",
                "     |# | o o | #|     ",
                "     |# |  -  | #| ... ",
                "      \\#'---'#/      ",
                "        ##<3##        ",
                "        ##  ##        ",
            )
        ),
        "sleepy": _ascii_frame(
            (
                "     <3           <3    ",
                "   .'  '.       .'  '.  ",
                "  /  zz  \\_^_/  zz  \\ ",
                "       .-#####-.   Zz  ",
                "      /# .---. #\\     ",
                "     |# | - - | #|     ",
                "     |# |  .  | #|     ",
                "      \\#'---'#/      ",
                "        ##<3##        ",
                "        ##  ##        ",
            )
        ),
    }


def write_default_buddy(destination: Path) -> Path:
    """Write a starter Buddy template folder."""
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "buddy.json"
    ascii_path = destination / "ascii_frames.json"
    manifest_path.write_text(json.dumps(default_manifest(), indent=2) + "\n", encoding="utf-8")
    ascii_path.write_text(json.dumps(default_ascii_frames(), indent=2) + "\n", encoding="utf-8")
    return manifest_path
