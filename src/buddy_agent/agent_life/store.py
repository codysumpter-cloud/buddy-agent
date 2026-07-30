"""Crash-safe local persistence and outbox for Agent Life state."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .runtime import AgentLifeError, STATE_SCHEMA

HOST_SCHEMA = "buddy.agent-life-host.v1"


class AgentLifeStore:
    """Persist runtime state and pending memory events as one atomic document."""

    def __init__(self, path: Path) -> None:
        self.path = path.expanduser().resolve()

    def load(self) -> dict[str, Any] | None:
        if not self.path.is_file():
            return None
        try:
            parsed = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise AgentLifeError("Agent Life host state is unreadable") from error
        if not isinstance(parsed, dict) or parsed.get("schema") != HOST_SCHEMA:
            raise AgentLifeError("Agent Life host state has an unsupported schema")
        state = parsed.get("state")
        pending = parsed.get("pending_memory_events")
        if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
            raise AgentLifeError("Agent Life runtime state is missing or unsupported")
        if not isinstance(pending, dict):
            raise AgentLifeError("Agent Life pending event state is invalid")
        return parsed

    def save(self, state: dict[str, Any], pending: dict[str, dict[str, Any]]) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "schema": HOST_SCHEMA,
                "state": state,
                "pending_memory_events": pending,
            },
            indent=2,
            sort_keys=True,
        ) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f".{self.path.name}-",
            suffix=".tmp",
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
        return self.path


class AgentLifeOutbox:
    """Write one immutable raw Agent Life event per file for Knowledge Vault ingestion."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory.expanduser().resolve()

    def write(self, event: dict[str, Any]) -> Path:
        event_id = str(event.get("event_id", ""))
        if not event_id:
            raise AgentLifeError("Agent Life memory event requires event_id")
        filename = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:24]
        target = self.directory / f"life-{filename}.json"
        content = json.dumps(event, indent=2, sort_keys=True) + "\n"
        self.directory.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_text(encoding="utf-8") != content:
                raise AgentLifeError("Agent Life outbox event ID collided with different content")
            return target
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.directory,
            prefix=f".{target.name}-",
            suffix=".tmp",
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if target.read_text(encoding="utf-8") != content:
                    raise AgentLifeError(
                        "Agent Life outbox event ID collided with different content"
                    ) from None
        finally:
            temporary.unlink(missing_ok=True)
        return target
