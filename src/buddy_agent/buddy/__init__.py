"""Buddy domain models, lifecycle helpers, and appearance contracts."""

from .appearance import BuddyAppearanceTemplate, BuddyFrameSpec, default_buddy_template
from .lifecycle import BuddyLifecycle, CareAction, CareResult
from .models import BuddyArchetype, BuddyProfile

__all__ = [
    "BuddyAppearanceTemplate",
    "BuddyArchetype",
    "BuddyFrameSpec",
    "BuddyLifecycle",
    "BuddyProfile",
    "CareAction",
    "CareResult",
    "default_buddy_template",
]
