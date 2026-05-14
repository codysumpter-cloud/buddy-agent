"""Local adapter implementations for the Buddy Agent scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .adapters import AdapterHealth, RetrievedSource
from .app_bridge import BuddyEvent, normalize_buddy_event_name
from .memory import NoteIndex
from .runtime.backends import LocalTemplateBackend, RuntimeBackend
from .runtime.types import RuntimeMessage


@dataclass
class LocalBuddyBrainAdapter:
    """Static startup context adapter for local development."""

    context: dict[str, str] = field(default_factory=dict)

    def health(self) -> AdapterHealth:
        """Return local adapter health."""
        return AdapterHealth(name="buddy-brain-local", ok=True, detail="static context")

    def load_startup_context(self) -> Mapping[str, str]:
        """Return configured startup context."""
        return dict(self.context)


@dataclass
class LocalOmniBuddyAdapter:
    """Local text router used when no remote Omni service is configured."""

    backend: RuntimeBackend = field(default_factory=LocalTemplateBackend)

    def health(self) -> AdapterHealth:
        """Return local adapter health."""
        return AdapterHealth(name="omni-local", ok=True, detail="callable local backend")

    def route_text(
        self,
        prompt: str,
        *,
        metadata: Mapping[str, str] | None = None,
        context: Sequence[str] = (),
    ) -> str:
        """Return a deterministic local backend response."""
        response = self.backend.respond(
            prompt,
            messages=(RuntimeMessage(role="user", content=prompt),),
            metadata=metadata,
            context=context,
        )
        return response.content


@dataclass
class LocalPrismtekAppBridge:
    """In-process app bridge for tests and local development."""

    events: list[BuddyEvent] = field(default_factory=list)

    def health(self) -> AdapterHealth:
        """Return local bridge health."""
        return AdapterHealth(name="prismtek-app-local", ok=True, detail="in-process events")

    def publish_event(self, event_name: str, payload: Mapping[str, object]) -> None:
        """Record a sanitized event name and string payload."""
        buddy_id = str(payload.get("buddy_id", "unknown"))
        body = {str(key): str(value) for key, value in payload.items() if key != "buddy_id"}
        self.events.append(
            BuddyEvent(name=normalize_buddy_event_name(event_name), buddy_id=buddy_id, body=body)
        )


@dataclass
class LocalKnowledgeVaultProvider:
    """Note-index backed retrieval provider for local development."""

    index: NoteIndex = field(default_factory=NoteIndex)

    def health(self) -> AdapterHealth:
        """Return local provider health."""
        return AdapterHealth(name="knowledge-vault-local", ok=True, detail="note index")

    def search(self, query: str, *, limit: int = 5) -> Sequence[RetrievedSource]:
        """Search local notes and return source-shaped results."""
        return tuple(
            RetrievedSource(
                source_id=record.note_id,
                title="Local note",
                text=record.text,
                metadata={"provider": "local"},
            )
            for record in self.index.find(query, limit=limit)
        )
