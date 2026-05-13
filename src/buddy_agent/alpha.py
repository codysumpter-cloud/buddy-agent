"""Buddy Agent Alpha Runtime.

This module composes scaffold pieces into a runnable local runtime. It is not full
feature parity with every reference repository yet, but it gives one tested path for
chat, memory, retrieval, skills, template validation, local routing, app bridge chat,
and companion policy.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from .adapters import (
    BuddyBrainAdapter,
    KnowledgeVaultProvider,
    PrismtekAppBridge,
    RetrievedSource,
)
from .app_bridge import BuddyAppChatRequest, BuddyAppChatResponse, IBeMoreSurface
from .buddy.generate import default_manifest
from .buddy.render_contract import validate_buddy_manifest
from .companion import (
    CompanionCapability,
    CompanionPermissionPolicy,
    CompanionShell,
    PermissionRequest,
)
from .config import BuddyAgentConfig
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
    """Runnable local Buddy Agent alpha runtime."""

    config: BuddyAgentConfig = field(default_factory=BuddyAgentConfig.from_env)
    engine: RuntimeEngine = field(default_factory=RuntimeEngine)
    memory: PersistentNoteIndex = field(default_factory=PersistentNoteIndex)
    skills: SkillRegistry = field(default_factory=SkillRegistry)
    omni: LocalOmniBuddyAdapter = field(default_factory=LocalOmniBuddyAdapter)
    permissions: CompanionPermissionPolicy = field(default_factory=CompanionPermissionPolicy)
    brain: BuddyBrainAdapter = field(
        default_factory=lambda: LocalBuddyBrainAdapter(
            context={
                "operator": "Buddy Alpha Runtime Plus local operator",
                "runbook": "route -> retrieve -> respond -> publish",
            }
        )
    )
    knowledge: KnowledgeVaultProvider | None = None
    app_bridge: PrismtekAppBridge = field(default_factory=LocalPrismtekAppBridge)
    companion_shell: CompanionShell = field(default_factory=CompanionShell.from_default_manifest)

    def __post_init__(self) -> None:
        if self.knowledge is None:
            self.knowledge = LocalKnowledgeVaultProvider(index=self.memory)
        self._register_builtin_skills()

    @classmethod
    def from_config(cls, config: BuddyAgentConfig) -> BuddyAlphaRuntime:
        """Create a runtime from explicit config."""
        brain = LocalBuddyBrainAdapter(
            context={
                "operator": config.operator_profile,
                "runbook": "load config -> retrieve memory -> route local model -> bridge app",
                "restricted_integrations": "disabled",
            }
        )
        return cls(
            config=config,
            memory=PersistentNoteIndex(config.resolved_memory_path),
            omni=LocalOmniBuddyAdapter.from_config(config.omni),
            brain=brain,
        )

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

    def operator_context(self) -> Mapping[str, str]:
        """Return Buddy Brain startup/operator context."""
        return self.brain.load_startup_context()

    def retrieve(self, query: str, *, limit: int = 3) -> tuple[RetrievedSource, ...]:
        """Search configured local retrieval providers."""
        if not self.config.retrieval_enabled:
            return ()
        provider = self.knowledge
        if provider is None:
            return ()
        return tuple(provider.search(query, limit=limit))

    def chat(self, prompt: str) -> AlphaRuntimeResult:
        """Send a prompt through the local runtime path."""
        self.engine.receive(prompt)
        recall = self.memory.find(prompt, limit=1)
        sources = self.retrieve(prompt, limit=2)
        context = self.operator_context()
        routed = self.omni.route_text(
            prompt,
            metadata={
                "session_id": self.engine.session_id,
                "operator": context.get("operator", self.config.operator_profile),
                "source_count": str(len(sources)),
            },
        )
        detail_parts: list[str] = []
        if recall:
            detail_parts.append(f"recall={recall[0].text}")
        if sources:
            source_titles = ", ".join(source.title for source in sources)
            detail_parts.append(f"sources={source_titles}")
        if context:
            detail_parts.append(f"operator={context.get('operator', 'local')}")
        return AlphaRuntimeResult(ok=True, message=routed, detail="; ".join(detail_parts))

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

    def load_companion_template(self, path: str | Path) -> AlphaRuntimeResult:
        """Load an app-safe Buddy template into the companion shell."""
        self.companion_shell = CompanionShell.load(path)
        return AlphaRuntimeResult(
            ok=True,
            message="companion template loaded",
            detail=self.companion_shell.source,
        )

    def app_chat(
        self,
        buddy_id: str,
        prompt: str,
        *,
        surface: IBeMoreSurface = "chat",
    ) -> BuddyAppChatResponse:
        """Handle one app bridge chat request and publish a sanitized event."""
        request = BuddyAppChatRequest(buddy_id=buddy_id, prompt=prompt, surface=surface)
        result = self.chat(request.prompt)
        self.app_bridge.publish_event(
            "buddy.updated",
            {
                "buddy_id": request.buddy_id,
                "surface": request.surface,
                "message": result.message,
            },
        )
        return BuddyAppChatResponse(
            ok=result.ok,
            buddy_id=request.buddy_id,
            message=result.message,
            detail=result.detail,
            payload={"surface": request.surface},
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

    def smoke(self) -> tuple[AlphaRuntimeResult, ...]:
        """Run alpha runtime checks."""
        app_response = self.app_chat("default-buddy", "hello from app bridge")
        return (
            self.validate_template(),
            self.chat("hello"),
            self.remember("Buddy Alpha Runtime is online."),
            self.recall("online"),
            self.run_skill("caps", "buddy"),
            self.request_companion_capability("chat", reason="smoke"),
            AlphaRuntimeResult(
                ok=app_response.ok,
                message="app bridge chat route ok",
                detail=app_response.buddy_id,
            ),
        )
