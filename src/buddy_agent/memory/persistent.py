"""File-backed note storage for the Alpha Runtime Plus path."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

from .index import NoteIndex, NoteRecord

DEFAULT_MEMORY_PATH = Path(
    os.getenv("BUDDY_MEMORY_FILE", "~/.buddy_agent/memory.json")
).expanduser()


class PersistentNoteIndex(NoteIndex):
    """A small JSON-backed note index.

    This keeps the Alpha Runtime useful across separate CLI calls without requiring a
    database or external service.
    """

    path: Path

    def __init__(self, path: Path | None = None) -> None:
        super().__init__()
        self.path = path or DEFAULT_MEMORY_PATH
        self.load()

    def load(self) -> None:
        """Load notes from disk if the file exists."""
        if not self.path.exists():
            return
        payload = cast(dict[str, Any], json.loads(self.path.read_text(encoding="utf-8")))
        records = cast(list[dict[str, Any]], payload.get("records", []))
        self.records = [
            NoteRecord(
                note_id=str(item["note_id"]),
                text=str(item["text"]),
                tags=tuple(str(tag) for tag in item.get("tags", [])),
            )
            for item in records
        ]

    def save(self) -> None:
        """Save notes to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "records": [
                {
                    "note_id": record.note_id,
                    "text": record.text,
                    "tags": list(record.tags),
                }
                for record in self.records
            ]
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def add(self, text: str, *, tags: tuple[str, ...] = ()) -> NoteRecord:
        """Add and persist one note."""
        record = super().add(text, tags=tags)
        self.save()
        return record
