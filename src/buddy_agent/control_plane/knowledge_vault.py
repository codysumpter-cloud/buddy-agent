"""Knowledge Vault emitter for sanitized Buddy runtime receipts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from .sanitizer import Sanitizer


ALLOWED_SOURCES = {"buddy-agent", "buddy-brain", "omni-buddy", "prismtek-apps", "knowledge-vault"}
ALLOWED_EVENT_TYPES = {
    "task_created",
    "task_completed",
    "decision_made",
    "repo_updated",
    "feature_added",
    "feature_removed",
    "model_changed",
    "concept_created",
    "concept_updated",
    "relationship_created",
}
EVENT_TYPE_BY_CLASS = {
    "task": "task_completed",
    "decision": "decision_made",
    "system": "repo_updated",
    "concept": "concept_created",
}


@dataclass(frozen=True)
class KnowledgeVaultEmitter:
    """Build and optionally write schema-shaped Knowledge Vault event drafts.

    The emitter writes only to an explicit local inbox path supplied by the
    caller. It never mutates compiled graph outputs and never creates network
    requests.
    """

    source: str = "buddy-agent"
    sanitizer: Sanitizer = field(default_factory=Sanitizer)

    def __post_init__(self) -> None:
        if self.source not in ALLOWED_SOURCES:
            raise ValueError(f"Unsupported Knowledge Vault source: {self.source}")

    def build_event(
        self,
        *,
        event_class: str,
        title: str,
        summary: str,
        payload: Mapping[str, Any] | None = None,
        event_type: str | None = None,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> Mapping[str, Any]:
        resolved_event_type = event_type or EVENT_TYPE_BY_CLASS.get(event_class)
        if resolved_event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unsupported Knowledge Vault event_type: {resolved_event_type}")

        safe_value, report = self.sanitizer.sanitize(payload or {})
        safe_payload = cast(Mapping[str, Any], safe_value)
        event: Mapping[str, Any] = {
            "event_id": event_id or f"evt-buddy-agent-{uuid4().hex[:16]}",
            "event_type": resolved_event_type,
            "source": self.source,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "payload": {
                "class": event_class,
                "title": title,
                "summary": summary,
                "adapter_status": "live-runtime-adapter",
                "redaction": {
                    "raw_prompts": "excluded",
                    "raw_traces": "excluded",
                    "secrets": "excluded",
                    "private_paths": "redacted",
                    "redacted_fields": list(report.redacted_fields),
                },
                **safe_payload,
            },
        }
        self.validate_event(event)
        return event

    def validate_event(self, event: Mapping[str, Any]) -> None:
        missing = [key for key in ("event_id", "event_type", "source", "timestamp", "payload") if key not in event]
        if missing:
            raise ValueError(f"Missing Knowledge Vault event fields: {', '.join(missing)}")
        if event["source"] not in ALLOWED_SOURCES:
            raise ValueError(f"Unsupported Knowledge Vault source: {event['source']}")
        if event["event_type"] not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unsupported Knowledge Vault event_type: {event['event_type']}")
        if not isinstance(event["payload"], Mapping):
            raise ValueError("Knowledge Vault event payload must be an object")
        self.sanitizer.assert_safe(event)

    def write_event(self, event: Mapping[str, Any], inbox_dir: str | Path) -> Path:
        self.validate_event(event)
        target_dir = Path(inbox_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        event_id = str(event["event_id"])
        target = target_dir / f"{event_id}.json"
        if target.exists():
            raise FileExistsError(f"Knowledge Vault event already exists: {target}")
        target.write_text(json.dumps(event, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target
