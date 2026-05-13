"""Small note index used by the scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class NoteRecord:
    """A stored note."""

    note_id: str
    text: str
    tags: tuple[str, ...] = ()


@dataclass
class NoteIndex:
    """Simple in-process note index."""

    records: list[NoteRecord] = field(default_factory=list)

    def add(self, text: str, *, tags: tuple[str, ...] = ()) -> NoteRecord:
        """Add one note."""
        record = NoteRecord(note_id=str(uuid4()), text=text, tags=tags)
        self.records.append(record)
        return record

    def find(self, query: str, *, limit: int = 5) -> tuple[NoteRecord, ...]:
        """Find notes containing query text."""
        normalized = query.lower().strip()
        if not normalized:
            return tuple(self.records[:limit])
        matches = [record for record in self.records if normalized in record.text.lower()]
        return tuple(matches[:limit])
