"""Omni/local runtime bridge boundaries for Buddy Agent."""

from .backend import CallableTextBackend, TextRouteBackend
from .config import OmniConfig, OmniRouteMode, OmniVisionMode

__all__ = [
    "CallableTextBackend",
    "OmniConfig",
    "OmniRouteMode",
    "OmniVisionMode",
    "TextRouteBackend",
]
