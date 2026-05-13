"""Buddy Agent Alpha Runtime.

This module composes scaffold pieces into a runnable local runtime. It is not full
feature parity with every reference repository yet, but it gives one tested path for
chat, memory, skills, template validation, local routing, and companion policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from .buddy.generate import default_manifest
from .buddy.render_contract import validate_buddy_manifest
from .companion import CompanionCapability, CompanionPermissionPolicy, PermissionRequest
from .local_adapters import LocalOmniBuddyAdapter
from .memory import NoteIndex
from .runtime import RuntimeEngine
from .skills import SkillDefinition, SkillRegistry


@dataclass
class AlphaRuntimeResult:
    """Result returned by the Alpha Runtime."""

    ok: bool
    message: str
    detail: str = ""


@dataclass
class BuddyAlphaRuntime:
    """Runnable local Buddy Agent alpha runtime."""

    engine: RuntimeEngine = field(default_factory=RuntimeEngine)
    memory: NoteIndex = field(default_factory=NoteIndex)
    skills: SkillRegistry = field(default_factory=SkillRegistry)
    omni: LocalOmniBuddyAdapter = field(default_factory=LocalOmniBuddyAdapter)
    permissions: CompanionPermissionPolicy = field(default_factory=CompanionPermissionPolicy)

    def __post_init__(self) -> None:
        self._register_builtin_skills()

    def _register_builtin_skills(self) -> None:
        """Register local alpha skills."""
        if "summarize" not in self.skills.names():
            self.skills.register(
                SkillDefinition(
                    name="summarize",
                    description="Return a compact local summary.",
                    handler=lambda text: text.strip()[:240],
                    metadata={"source": "alpha-runtime"},
                )
            )
        if "caps" not in self.skills.names():
            self.skills.register(
                SkillDefinition(
                    name="caps",
                    description="Uppercase input text.",
                    handler=lambda text: text.upper(),
                    metadata={"source": "alpha-runtime"},
                )
            )

    def chat(self, prompt: str) -> AlphaRuntimeResult:
        """Send a prompt through the local runtime path."""
        self.engine.receive(prompt)
        recall = self.memory.find(prompt, limit=1)
        recall_text = f" recall={recall[0].text}" if recall else ""
        routed = self.omni.route_text(prompt)
        return AlphaRuntimeResult(ok=True, message=routed, detail=recall_text)

    def remember(self, text: str) -> AlphaRuntimeResult:
        """Store a memory note."""
        record = self.memory.add(text, tags=("alpha",))
        return AlphaRuntimeResult(ok=True, message="memory saved", detail=record.note_id)

    def recall(self, query: str) -> AlphaRuntimeResult:
        """Search memory notes."""
        matches = self.memory.find(query)
        if not matches:
            return AlphaRuntimeResult(ok=True, message="no memories found")
        return AlphaRuntimeResult(ok=True, message="\n".join(record.text for record in matches))

    def run_skill(self, name: str, text: str) -> AlphaRuntimeResult:
        """Run a registered skill."""
        output = self.skills.run(name, text)
        return AlphaRuntimeResult(ok=True, message=output)

    def validate_template(self) -> AlphaRuntimeResult:
        """Validate the default Buddy template manifest."""
        validate_buddy_manifest(default_manifest())
        return AlphaRuntimeResult(ok=True, message="default Buddy template valid")

    def request_companion_capability(self, capability: str, *, reason: str) -> AlphaRuntimeResult:
        """Check companion permission policy for a capability name."""
        request = PermissionRequest(
            capability=cast(CompanionCapability, capability),
            reason=reason,
            user_initiated=True,
        )
        decision = self.permissions.decide(request)
        return AlphaRuntimeResult(ok=True, message=decision.decision, detail=decision.reason)

    def smoke(self) -> tuple[AlphaRuntimeResult, ...]:
        """Run alpha runtime checks."""
        return (
            self.validate_template(),
            self.chat("hello"),
            self.remember("Buddy Alpha Runtime is online."),
            self.recall("online"),
            self.run_skill("caps", "buddy"),
            self.request_companion_capability("chat", reason="smoke"),
        )
