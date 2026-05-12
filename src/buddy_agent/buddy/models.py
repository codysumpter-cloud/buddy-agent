"""Buddy product-domain models used by the runtime and app bridge."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BuddyArchetype:
    """A reusable Buddy starting template."""

    key: str
    name: str
    description: str
    default_traits: tuple[str, ...] = ()


@dataclass
class BuddyProfile:
    """A runtime-safe Buddy profile.

    This is intentionally small. App-specific UI state and secrets should stay outside this model.
    """

    buddy_id: str
    display_name: str
    archetype: BuddyArchetype
    mood: str = "steady"
    energy: int = 100
    attention: int = 100
    proficiencies: dict[str, int] = field(default_factory=dict)

    def clamp_stats(self) -> None:
        """Clamp mutable care stats to a safe 0-100 range."""
        self.energy = max(0, min(100, self.energy))
        self.attention = max(0, min(100, self.attention))
