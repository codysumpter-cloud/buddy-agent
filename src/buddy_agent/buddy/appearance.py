"""Buddy appearance contracts and validation.

A Buddy is the pet-like animated companion that lives inside the app. The phone,
web UI, HUD, or terminal is the device. The Buddy itself is not a device.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RenderMode = Literal["pixel", "ascii"]
BuddyState = Literal["idle", "happy", "thinking", "sleepy"]

BUDDY_CANVAS_SIZE = 64
BUDDY_ANIMATION_STATES: tuple[BuddyState, ...] = ("idle", "happy", "thinking", "sleepy")
BUDDY_RENDER_MODES: tuple[RenderMode, ...] = ("pixel", "ascii")


@dataclass(frozen=True)
class BuddyFrameSpec:
    """A single required Buddy animation frame."""

    state: BuddyState
    width: int = BUDDY_CANVAS_SIZE
    height: int = BUDDY_CANVAS_SIZE
    centered: bool = True
    equal_padding: bool = True

    def validate(self) -> None:
        """Validate frame constraints used by the app renderer."""
        if self.width != BUDDY_CANVAS_SIZE or self.height != BUDDY_CANVAS_SIZE:
            raise ValueError("Buddy frames must use a 64x64 canvas")
        if self.state not in BUDDY_ANIMATION_STATES:
            raise ValueError(f"Unsupported Buddy state: {self.state}")
        if not self.centered:
            raise ValueError("Buddy frames must be centered")
        if not self.equal_padding:
            raise ValueError("Buddy frames must keep equal padding")


@dataclass(frozen=True)
class BuddyAppearanceTemplate:
    """Template metadata for generated Buddy appearances."""

    key: str
    display_name: str
    modes: tuple[RenderMode, ...] = BUDDY_RENDER_MODES
    states: tuple[BuddyState, ...] = BUDDY_ANIMATION_STATES
    canvas_size: int = BUDDY_CANVAS_SIZE
    palette: tuple[str, ...] = (
        "#08165c",  # deep navy outline
        "#56d6d2",  # cyan shadow
        "#8ee9df",  # mint body
        "#cffff2",  # face panel
        "#effff9",  # highlight
        "#ffd45e",  # gold heart
        "#f69c45",  # warm heart shadow
        "#f8fbff",  # eye highlight
    )
    traits: tuple[str, ...] = (
        "tama-like",
        "pet",
        "cute",
        "trainable",
        "round_mint_body",
        "heart_antler_ears",
        "top_tuft",
        "face_panel",
        "tiny_arms_and_feet",
        "gold_heart_charm",
        "navy_pixel_outline",
        "transparent_background",
    )
    customization_options: tuple[str, ...] = (
        "palette",
        "heart_antler_ears",
        "tuft",
        "face_panel",
        "belly_heart_charm",
        "accessory",
        "pose",
        "outline_weight",
        "highlight_pattern",
        "idle_animation",
        "ascii_style",
    )
    frames: tuple[BuddyFrameSpec, ...] = field(
        default_factory=lambda: tuple(
            BuddyFrameSpec(state=state) for state in BUDDY_ANIMATION_STATES
        )
    )

    def validate(self) -> None:
        """Validate template constraints for app-safe rendering."""
        if self.canvas_size != BUDDY_CANVAS_SIZE:
            raise ValueError("Buddy templates must use a 64x64 canvas")
        if tuple(self.states) != BUDDY_ANIMATION_STATES:
            raise ValueError("Buddy templates must define idle, happy, thinking, and sleepy states")
        if tuple(self.modes) != BUDDY_RENDER_MODES:
            raise ValueError("Buddy templates must support pixel and ascii modes")
        for frame in self.frames:
            frame.validate()


def default_buddy_template() -> BuddyAppearanceTemplate:
    """Return the built-in default Buddy appearance template."""
    template = BuddyAppearanceTemplate(key="default-buddy", display_name="Default Buddy")
    template.validate()
    return template
