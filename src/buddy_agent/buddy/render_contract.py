"""App renderer contract for Buddy appearance manifests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .appearance import BUDDY_ANIMATION_STATES, BUDDY_CANVAS_SIZE, BUDDY_RENDER_MODES


class BuddyRenderContractError(ValueError):
    """Raised when a Buddy appearance manifest cannot be rendered safely."""


def require_mapping(value: object, *, name: str) -> Mapping[str, object]:
    """Return a mapping or raise a contract error."""
    if not isinstance(value, Mapping):
        raise BuddyRenderContractError(f"{name} must be an object")
    return value


def require_sequence(value: object, *, name: str) -> Sequence[object]:
    """Return a sequence or raise a contract error."""
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise BuddyRenderContractError(f"{name} must be a list")
    return value


def validate_buddy_manifest(manifest: Mapping[str, object]) -> None:
    """Validate the app-facing Buddy appearance manifest."""
    canvas = require_mapping(manifest.get("canvas"), name="canvas")
    if canvas.get("width") != BUDDY_CANVAS_SIZE or canvas.get("height") != BUDDY_CANVAS_SIZE:
        raise BuddyRenderContractError("canvas must be 64x64")

    render_modes = tuple(require_sequence(manifest.get("render_modes"), name="render_modes"))
    if render_modes != BUDDY_RENDER_MODES:
        raise BuddyRenderContractError("render_modes must be pixel and ascii")

    states = tuple(require_sequence(manifest.get("states"), name="states"))
    if states != BUDDY_ANIMATION_STATES:
        raise BuddyRenderContractError("states must be idle, happy, thinking, sleepy")

    rules = require_mapping(manifest.get("rules"), name="rules")
    if rules.get("buddy_is_pet") is not True:
        raise BuddyRenderContractError("buddy_is_pet must be true")
    if rules.get("device_shape_allowed") is not False:
        raise BuddyRenderContractError("device_shape_allowed must be false")
    if rules.get("centered") is not True:
        raise BuddyRenderContractError("centered must be true")
    if rules.get("equal_padding") is not True:
        raise BuddyRenderContractError("equal_padding must be true")

    assets = require_mapping(manifest.get("assets"), name="assets")
    for key in ("app_icon", "default_pixel", "readme_mascot"):
        if not isinstance(assets.get(key), str):
            raise BuddyRenderContractError(f"assets.{key} must be a path")
