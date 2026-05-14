"""JSON storage for Buddy Training progress."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import BuddyTrainingState


def default_training_path() -> Path:
    configured = os.environ.get("BUDDY_TRAINING_STATE")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".buddy-agent" / "training-state.json"


class BuddyTrainingStore:
    """JSON-backed local progress store."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_training_path()

    def load(self) -> BuddyTrainingState:
        if not self.path.exists():
            return BuddyTrainingState()
        raw: Any = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Buddy Training state must be a JSON object: {self.path}")
        return BuddyTrainingState.from_dict(raw)

    def save(self, state: BuddyTrainingState) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n"
        self.path.write_text(body, encoding="utf-8")
        return self.path

    def reset(self) -> BuddyTrainingState:
        state = BuddyTrainingState()
        self.save(state)
        return state
