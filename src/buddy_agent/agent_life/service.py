"""Buddy Agent host service for persistent Agent Life state."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .runtime import AgentLifeError, AgentLifeRuntime
from .store import AgentLifeOutbox, AgentLifeStore


class AgentLifeService:
    """Coordinate immutable profile, atomic state, and durable memory publication."""

    def __init__(self, profile: Mapping[str, Any], store: AgentLifeStore, outbox: AgentLifeOutbox) -> None:
        self.store = store
        self.outbox = outbox
        envelope = store.load()
        snapshot = envelope["state"] if envelope is not None else None
        self.pending: dict[str, dict[str, Any]] = (
            dict(envelope["pending_memory_events"]) if envelope is not None else {}
        )
        self.runtime = AgentLifeRuntime(profile, snapshot)
        if envelope is None:
            self.store.save(self.runtime.snapshot(), self.pending)
        self.flush_pending()

    @classmethod
    def from_paths(cls, profile_path: Path, state_path: Path, outbox_dir: Path) -> AgentLifeService:
        try:
            parsed = json.loads(profile_path.expanduser().read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise AgentLifeError("compiled Agent Life profile is unreadable") from error
        if not isinstance(parsed, dict):
            raise AgentLifeError("compiled Agent Life profile must be a JSON object")
        return cls(parsed, AgentLifeStore(state_path), AgentLifeOutbox(outbox_dir))

    def apply_outcome(self, event: Mapping[str, Any]) -> dict[str, Any]:
        before = self.runtime.snapshot()
        result = self.runtime.apply_event(event)
        if not result["applied"]:
            return result
        memory_event = result["memory_event"]
        assert isinstance(memory_event, dict)
        event_id = str(memory_event["event_id"])
        self.pending[event_id] = memory_event
        try:
            self.store.save(self.runtime.snapshot(), self.pending)
        except Exception:
            del self.pending[event_id]
            self.runtime.restore(before)
            raise

        # Once the state+pending marker is durable, never roll the learning back in
        # memory. A publication failure is recoverable by flush_pending() on restart.
        outbox_path = self.outbox.write(memory_event)
        del self.pending[event_id]
        try:
            self.store.save(self.runtime.snapshot(), self.pending)
        except Exception:
            self.pending[event_id] = memory_event
            raise
        result["outbox_path"] = str(outbox_path)
        return result

    def flush_pending(self) -> list[Path]:
        published: list[Path] = []
        changed = False
        for event_id, event in list(self.pending.items()):
            published.append(self.outbox.write(event))
            del self.pending[event_id]
            changed = True
        if changed:
            self.store.save(self.runtime.snapshot(), self.pending)
        return published

    def advance(self, elapsed_hours: float, now: str) -> dict[str, Any]:
        state = self.runtime.advance(elapsed_hours, now)
        self.store.save(state, self.pending)
        return state

    def status(self) -> dict[str, Any]:
        state = self.runtime.snapshot()
        return {
            "schema": "buddy.agent-life-status.v1",
            "agent_id": self.runtime.agent_id,
            "profile_sha256": self.runtime.profile_hash,
            "development": state["development"],
            "drives": state["drives"],
            "traits": state["traits"],
            "preference_count": len(state["preferences"]),
            "relationship_count": len(state["relationships"]),
            "pending_memory_events": len(self.pending),
            "claim_boundary": (
                "These are functional developmental states, not proof of consciousness or suffering."
            ),
        }
