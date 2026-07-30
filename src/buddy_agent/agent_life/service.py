"""Buddy Agent host service for persistent Agent Life state."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from buddy_agent.tasks.models import TERMINAL_STATUSES, TaskRecord

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

    def apply_task_outcome(
        self,
        task: TaskRecord,
        *,
        authority_kind: str,
        authority_id: str,
        evidence: list[Mapping[str, str]],
        subject_id: str | None = None,
    ) -> dict[str, Any]:
        """Admit a terminal task only after an external authority cites evidence."""
        if task.status not in TERMINAL_STATUSES or task.status == "cancelled":
            raise AgentLifeError("Agent Life can learn only from completed or failed tasks")
        if not evidence:
            raise AgentLifeError("task outcome requires at least one sanitized evidence reference")
        outcome_kind = "task_succeeded" if task.status == "completed" else "task_failed"
        reward = 1.0 if task.status == "completed" else -1.0
        workflow_id = subject_id.strip() if subject_id else f"buddy-task:{task.risk}"
        if not workflow_id:
            raise AgentLifeError("task outcome subject_id cannot be empty")
        return self.apply_outcome(
            {
                "id": f"{task.id}:{task.revision}:{task.status}",
                "kind": outcome_kind,
                "occurred_at": task.updated_at,
                "subject": {"type": "workflow", "id": workflow_id},
                "reward": reward,
                "confidence": 1.0,
                "significance": max(1.0, len(task.plan) / 2.0),
                "authority": {"kind": authority_kind, "actor_id": authority_id},
                "evidence": [dict(item) for item in evidence],
            }
        )

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
