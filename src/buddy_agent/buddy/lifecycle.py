"""Buddy lifecycle helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import BuddyProfile

CareAction = Literal["feed", "play", "rest", "train"]


@dataclass(frozen=True)
class CareResult:
    """Result of applying a care action."""

    action: CareAction
    energy_delta: int
    attention_delta: int
    mood: str


class BuddyLifecycle:
    """Deterministic care and training logic for Buddy profiles."""

    def apply_care(self, profile: BuddyProfile, action: CareAction) -> CareResult:
        """Apply a care action to a Buddy profile."""
        if action == "feed":
            result = CareResult(action=action, energy_delta=15, attention_delta=2, mood="content")
        elif action == "play":
            result = CareResult(action=action, energy_delta=-5, attention_delta=15, mood="bright")
        elif action == "rest":
            result = CareResult(action=action, energy_delta=25, attention_delta=-2, mood="calm")
        else:
            result = CareResult(action=action, energy_delta=-10, attention_delta=8, mood="focused")

        profile.energy += result.energy_delta
        profile.attention += result.attention_delta
        profile.mood = result.mood
        profile.clamp_stats()
        return result

    def train(self, profile: BuddyProfile, proficiency: str, amount: int = 1) -> int:
        """Increase a Buddy proficiency and return the new value."""
        if amount < 1:
            raise ValueError("Training amount must be positive")
        current = profile.proficiencies.get(proficiency, 0)
        updated = min(100, current + amount)
        profile.proficiencies[proficiency] = updated
        profile.energy = max(0, profile.energy - 1)
        return updated
