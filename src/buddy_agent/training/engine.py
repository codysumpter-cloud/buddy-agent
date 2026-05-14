"""Deterministic Buddy Training reward engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import BuddyTrainingState, TrainingAction


@dataclass(frozen=True)
class TrainingReward:
    """Reward emitted by a Buddy Training action."""

    xp: int
    sparks: int = 0
    snacks: int = 0
    stat_deltas: dict[str, int] = field(default_factory=dict)
    achievements: tuple[str, ...] = ()
    cosmetics: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrainingApplyResult:
    """Result of applying a training reward."""

    state: BuddyTrainingState
    reward: TrainingReward
    levels_gained: int
    new_achievements: tuple[str, ...]
    new_cosmetics: tuple[str, ...]


BASE_REWARDS: dict[TrainingAction, TrainingReward] = {
    "chat": TrainingReward(xp=5, stat_deltas={"bond": 1, "curiosity": 1}),
    "remember": TrainingReward(xp=8, sparks=1, stat_deltas={"bond": 1, "reliability": 1}),
    "recall": TrainingReward(xp=8, stat_deltas={"focus": 1, "reliability": 1}),
    "skill_used": TrainingReward(xp=10, sparks=1, stat_deltas={"focus": 1, "creativity": 1}),
    "quest_completed": TrainingReward(
        xp=24,
        sparks=3,
        snacks=1,
        stat_deltas={"discipline": 2, "reliability": 2, "bond": 1},
    ),
    "test_passed": TrainingReward(xp=18, sparks=2, stat_deltas={"reliability": 2, "focus": 1}),
    "doc_added": TrainingReward(xp=12, sparks=1, stat_deltas={"curiosity": 2}),
    "code_reviewed": TrainingReward(
        xp=16,
        sparks=2,
        stat_deltas={"discipline": 1, "reliability": 1, "creativity": 1},
    ),
    "memory_reviewed": TrainingReward(xp=14, sparks=1, stat_deltas={"focus": 1, "bond": 1}),
    "approval_handled": TrainingReward(xp=12, stat_deltas={"discipline": 2, "autonomy": 1}),
}


def xp_needed_for_next_level(level: int) -> int:
    """Return XP required to advance from a level."""
    return 50 + max(1, level) * 25


def reward_for_action(action: TrainingAction) -> TrainingReward:
    """Return the deterministic reward for a training action."""
    return BASE_REWARDS[action]


class BuddyTrainingEngine:
    """Apply Buddy Training actions to local progression state."""

    def apply(self, state: BuddyTrainingState, action: TrainingAction) -> TrainingApplyResult:
        """Apply a training action and return the updated state."""
        reward = reward_for_action(action)
        before_achievements = set(state.achievements)
        before_cosmetics = set(state.cosmetics)

        state.xp += reward.xp
        state.lifetime_xp += reward.xp
        state.sparks += reward.sparks
        state.snacks += reward.snacks
        state.last_action = action

        for stat_name, delta in reward.stat_deltas.items():
            current = getattr(state.stats, stat_name)
            setattr(state.stats, stat_name, current + delta)
        state.stats.clamp()

        levels_gained = self._apply_leveling(state)
        self._apply_unlocks(state)

        new_achievements = tuple(sorted(state.achievements - before_achievements))
        new_cosmetics = tuple(sorted(state.cosmetics - before_cosmetics))
        return TrainingApplyResult(
            state=state,
            reward=reward,
            levels_gained=levels_gained,
            new_achievements=new_achievements,
            new_cosmetics=new_cosmetics,
        )

    def summary_lines(self, state: BuddyTrainingState) -> tuple[str, ...]:
        """Return CLI-friendly summary lines for a training state."""
        stats = state.stats.to_dict()
        stat_summary = ", ".join(f"{name}={value}" for name, value in stats.items())
        return (
            f"Buddy Training: {state.buddy_id}",
            f"level={state.level} xp={state.xp}/{xp_needed_for_next_level(state.level)} lifetime_xp={state.lifetime_xp}",
            f"evolution={state.evolution} sparks={state.sparks} snacks={state.snacks}",
            f"stats: {stat_summary}",
            f"achievements: {', '.join(sorted(state.achievements)) or 'none'}",
            f"cosmetics: {', '.join(sorted(state.cosmetics)) or 'none'}",
            f"last_action={state.last_action}",
        )

    def _apply_leveling(self, state: BuddyTrainingState) -> int:
        levels_gained = 0
        while state.xp >= xp_needed_for_next_level(state.level):
            state.xp -= xp_needed_for_next_level(state.level)
            state.level += 1
            levels_gained += 1
        return levels_gained

    def _apply_unlocks(self, state: BuddyTrainingState) -> None:
        if state.lifetime_xp >= 25:
            state.achievements.add("first-sparks")
        if state.level >= 2:
            state.cosmetics.add("tiny-hat")
            state.evolution = "apprentice"
        if state.level >= 4:
            state.achievements.add("steady-helper")
            state.cosmetics.add("workshop-scarf")
            state.evolution = "specialist"
        if state.level >= 8:
            state.achievements.add("guardian-buddy")
            state.cosmetics.add("guardian-cape")
            state.evolution = "guardian"
        if state.stats.reliability >= 10:
            state.achievements.add("reliable-runtime")
        if state.stats.bond >= 10:
            state.achievements.add("bonded-buddy")
