"""Typed Buddy Training state models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, cast

TrainingAction = Literal[
    "chat",
    "remember",
    "recall",
    "skill_used",
    "quest_completed",
    "test_passed",
    "doc_added",
    "code_reviewed",
    "memory_reviewed",
    "approval_handled",
]

EvolutionStage = Literal["seedling", "apprentice", "specialist", "guardian"]
ALLOWED_TRAINING_ACTIONS: tuple[TrainingAction, ...] = (
    "chat",
    "remember",
    "recall",
    "skill_used",
    "quest_completed",
    "test_passed",
    "doc_added",
    "code_reviewed",
    "memory_reviewed",
    "approval_handled",
)
STAT_NAMES = (
    "bond",
    "focus",
    "curiosity",
    "discipline",
    "creativity",
    "reliability",
    "autonomy",
)


@dataclass
class BuddyTrainingStats:
    """Local growth stats for Buddy Training."""

    bond: int = 1
    focus: int = 1
    curiosity: int = 1
    discipline: int = 1
    creativity: int = 1
    reliability: int = 1
    autonomy: int = 1

    def clamp(self) -> None:
        for name in STAT_NAMES:
            value = getattr(self, name)
            setattr(self, name, max(0, min(100, value)))

    def to_dict(self) -> dict[str, int]:
        return {name: int(getattr(self, name)) for name in STAT_NAMES}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> BuddyTrainingStats:
        stats = cls(
            bond=_int_value(data.get("bond"), default=1),
            focus=_int_value(data.get("focus"), default=1),
            curiosity=_int_value(data.get("curiosity"), default=1),
            discipline=_int_value(data.get("discipline"), default=1),
            creativity=_int_value(data.get("creativity"), default=1),
            reliability=_int_value(data.get("reliability"), default=1),
            autonomy=_int_value(data.get("autonomy"), default=1),
        )
        stats.clamp()
        return stats


@dataclass
class BuddyTrainingState:
    """Persisted local Buddy Training state."""

    buddy_id: str = "default"
    level: int = 1
    xp: int = 0
    lifetime_xp: int = 0
    sparks: int = 0
    snacks: int = 0
    stats: BuddyTrainingStats = field(default_factory=BuddyTrainingStats)
    achievements: set[str] = field(default_factory=set)
    cosmetics: set[str] = field(default_factory=set)
    evolution: EvolutionStage = "seedling"
    last_action: str = "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "buddy_id": self.buddy_id,
            "level": self.level,
            "xp": self.xp,
            "lifetime_xp": self.lifetime_xp,
            "sparks": self.sparks,
            "snacks": self.snacks,
            "stats": self.stats.to_dict(),
            "achievements": sorted(self.achievements),
            "cosmetics": sorted(self.cosmetics),
            "evolution": self.evolution,
            "last_action": self.last_action,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> BuddyTrainingState:
        raw_stats = data.get("stats")
        stats = BuddyTrainingStats.from_dict(raw_stats if isinstance(raw_stats, dict) else {})
        state = cls(
            buddy_id=str(data.get("buddy_id") or "default"),
            level=max(1, _int_value(data.get("level"), default=1)),
            xp=max(0, _int_value(data.get("xp"), default=0)),
            lifetime_xp=max(0, _int_value(data.get("lifetime_xp"), default=0)),
            sparks=max(0, _int_value(data.get("sparks"), default=0)),
            snacks=max(0, _int_value(data.get("snacks"), default=0)),
            stats=stats,
            achievements=_string_set(data.get("achievements")),
            cosmetics=_string_set(data.get("cosmetics")),
            evolution=_evolution_value(data.get("evolution")),
            last_action=str(data.get("last_action") or "none"),
        )
        state.stats.clamp()
        return state


def parse_training_action(value: str) -> TrainingAction:
    if value not in ALLOWED_TRAINING_ACTIONS:
        supported = ", ".join(ALLOWED_TRAINING_ACTIONS)
        raise ValueError(f"Unsupported Buddy Training action: {value}. Supported: {supported}")
    return cast(TrainingAction, value)


def _int_value(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def _evolution_value(value: object) -> EvolutionStage:
    if value in {"seedling", "apprentice", "specialist", "guardian"}:
        return cast(EvolutionStage, value)
    return "seedling"
