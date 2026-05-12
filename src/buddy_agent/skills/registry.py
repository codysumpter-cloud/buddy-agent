"""Skill registry primitives."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

SkillHandler = Callable[[str], str]


@dataclass(frozen=True)
class SkillDefinition:
    """A callable skill exposed to the runtime."""

    name: str
    description: str
    handler: SkillHandler
    metadata: Mapping[str, str]


class SkillRegistry:
    """Registry for runtime skills."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillDefinition] = {}

    def register(self, definition: SkillDefinition) -> None:
        """Register a skill."""
        if definition.name in self._skills:
            raise ValueError(f"Skill already registered: {definition.name}")
        self._skills[definition.name] = definition

    def names(self) -> tuple[str, ...]:
        """Return skill names in stable order."""
        return tuple(sorted(self._skills))

    def run(self, name: str, input_text: str) -> str:
        """Run a skill by name."""
        definition = self._skills.get(name)
        if definition is None:
            raise KeyError(name)
        return definition.handler(input_text)
