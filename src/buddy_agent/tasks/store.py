"""Atomic local storage for Buddy task records."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import cast

from buddy_agent.receipts.record import JSONValue

from .models import TaskRecord

DEFAULT_TASKS_DIR = Path(os.getenv("BUDDY_TASKS_DIR", "~/.buddy_agent/tasks")).expanduser()
TASK_ID = re.compile(r"^task-[a-f0-9]{24}$")


class TaskStoreError(ValueError):
    """Safe task storage failure."""


class TaskStore:
    """Store one JSON document per task with atomic replacement."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = (directory or DEFAULT_TASKS_DIR).expanduser().resolve()

    def _path(self, task_id: str) -> Path:
        if not TASK_ID.fullmatch(task_id):
            raise TaskStoreError("invalid Buddy task id")
        return self.directory / f"{task_id}.json"

    def save(self, task: TaskRecord) -> Path:
        """Atomically persist one task record."""
        path = self._path(task.id)
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(task.to_dict(), indent=2, sort_keys=True) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.directory,
            prefix=f".{task.id}-",
            suffix=".tmp",
            text=True,
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return path

    def load(self, task_id: str) -> TaskRecord:
        """Load one task or raise a safe not-found error."""
        path = self._path(task_id)
        if not path.is_file():
            raise TaskStoreError(f"unknown Buddy task: {task_id}")
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise TaskStoreError(f"task state is unreadable: {task_id}") from error
        if not isinstance(parsed, dict) or parsed.get("schema") != "buddy.task.v1":
            raise TaskStoreError(f"task state has an unsupported schema: {task_id}")
        return TaskRecord.from_dict(cast(dict[str, JSONValue], parsed))

    def list(self) -> list[TaskRecord]:
        """Load all valid task records newest-first."""
        if not self.directory.is_dir():
            return []
        tasks: list[TaskRecord] = []
        for path in self.directory.glob("task-*.json"):
            try:
                tasks.append(self.load(path.stem))
            except TaskStoreError:
                continue
        return sorted(tasks, key=lambda task: (task.updated_at, task.id), reverse=True)

    def exists(self, task_id: str) -> bool:
        return self._path(task_id).is_file()
