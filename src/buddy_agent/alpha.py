"""Buddy Agent Alpha Runtime Plus.

This module composes the first native-port milestone into one runnable local
runtime. It is not full feature parity with every reference repository yet. It wires
Buddy-native runtime config, a callable backend path, persistent memory, retrieval,
Buddy Brain operator context, a Prismtek app bridge, Buddy template loading, skills,
and companion permission policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from .buddy.generate import default_manifest
from .buddy.render_contract import validate_buddy_manifest
from .companion import (
    CompanionCapability,
    CompanionPermissionPolicy,
    CompanionShell,
    PermissionRequest,
    load_companion_shell,
)
from .local_adapters import (
    LocalBuddyBrainAdapter,
    LocalKnowledgeVaultProvider,
    LocalOmniBuddyAdapter,
    LocalPrismtekAppBridge,
)
from .memory import PersistentNoteIndex
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
    """Runnable local Buddy Agent Alpha Runtime Plus."""

    engine: RuntimeEngine = field(default_factory=RuntimeEngine)
    memory: PersistentNoteIndex = field(default_factory=PersistentNoteIndex)
    skills: SkillRegistry = field(default_factory=SkillRegistry)
    brain: LocalBuddyBrainAdapter = field(
        default_factory=lambda: LocalBuddyBrainAdapter(
            context={
                "operator": "buddy-brain-local",
                "posture": "helpful, consent-first, no restricted automation by default",
            }
        )
    )
    omni: LocalOmniBuddyAdapter = field(default_factory=LocalOmniBuddyAdapter)
    vault: LocalKnowledgeVaultProvider = field(default_factory=LocalKnowledgeVaultProvider)
    app_bridge: LocalPrismtekAppBridge = field(default_factory=LocalPrismtekAppBridge)
    permissions: CompanionPermissionPolicy = field(default_factory=CompanionPermissionPolicy)
    companion_shell: CompanionShell = field(default_factory=load_companion_shell)

    def __post_init__(self) -> None:
        self.vault.index = self.memory
        self._register_builtin_skills()

    def _register_builtin_skills(self) -> None:
        """Register local alpha skills."""
        if "summarize" not in self.skills.names():
            self.skills.register(
                SkillDefinition(
                    name="summarize",
                    description="Return a compact local summary.",
                    handler=lambda text: text.strip()[:240],
                    metadata={"source": "alpha-runtime-plus"},
                )
            )
        if "caps" not in self.skills.names():
            self.skills.register(
                SkillDefinition(
                    name="caps",
                    description="Uppercase input text.",
                    handler=lambda text: text.upper(),
                    metadata={"source": "alpha-runtime-plus"},
                )
            )

    def _retrieval_context(self, prompt: str) -> tuple[str, ...]:
        """Build backend context from Buddy Brain and local retrieval providers."""
        brain_context = tuple(
            f"buddy_brain.{key}={value}"
            for key, value in self.brain.load_startup_context().items()
        )
        sources = self.vault.search(prompt, limit=self.engine.config.memory_limit)
        retrieved = tuple(f"{source.title}: {source.text}" for source in sources)
        return brain_context + retrieved

    def chat(self, prompt: str) -> AlphaRuntimeResult:
        """Send a prompt through the integrated local runtime path."""
        context = self._retrieval_context(prompt)
        message = self.engine.receive(
            prompt,
            metadata={"route": "alpha.chat", "buddy_id": self.companion_shell.buddy_id},
            context=context,
        )
        self.app_bridge.publish_event(
            "buddy.updated",
            {
                "buddy_id": self.companion_shell.buddy_id,
                "route": "alpha.chat",
                "response": message,
            },
        )
        detail = f"sources={len(context)} events={len(self.app_bridge.events)}"
        return AlphaRuntimeResult(ok=True, message=message, detail=detail)

    def remember(self, text: str) -> AlphaRuntimeResult:
        """Store a memory note."""
        record = self.memory.add(text, tags=("alpha", "buddy"))
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
        """Validate the default Buddy template manifest and companion shell."""
        validate_buddy_manifest(default_manifest())
        states = ",".join(self.companion_shell.state_names())
        return AlphaRuntimeResult(
            ok=True,
            message="default Buddy template valid",
            detail=f"companion={self.companion_shell.display_name} states={states}",
        )

    def request_companion_capability(self, capability: str, *, reason: str) -> AlphaRuntimeResult:
        """Check companion permission policy for a capability name."""
        request = PermissionRequest(
            capability=cast(CompanionCapability, capability),
            reason=reason,
            user_initiated=True,
        )
        decision = self.permissions.decide(request)
        return AlphaRuntimeResult(ok=True, message=decision.decision, detail=decision.reason)

    def route_app_chat(self, prompt: str, *, surface: str = "local") -> AlphaRuntimeResult:
        """Run one app-bridge chat turn through the same runtime path."""
        self.app_bridge.publish_event(
            "buddy.updated",
            {
                "buddy_id": self.companion_shell.buddy_id,
                "surface": surface,
                "route": "app.chat.requested",
            },
        )
        return self.chat(prompt)

    def smoke(self) -> tuple[AlphaRuntimeResult, ...]:
        """Run alpha runtime checks."""
        remembered = self.remember("Buddy Alpha Runtime Plus retrieval is online.")
        return (
            self.validate_template(),
            remembered,
            self.recall("retrieval"),
            self.chat("retrieval"),
            self.run_skill("caps", "buddy"),
            self.route_app_chat("hello from app bridge", surface="test"),
            self.request_companion_capability("chat", reason="smoke"),
        )
