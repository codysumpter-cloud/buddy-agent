"""Sanitized task economics records for routing feedback and receipts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

SecurityGate = Literal["pass", "review", "block", "not-run"]


@dataclass(frozen=True)
class TaskEconomics:
    task_id: str
    provider: str
    model: str
    attempts: int
    model_cost: float
    tool_cost: float
    elapsed_ms: int
    human_review_minutes: float
    verification_passed: bool
    artifacts_accepted: bool
    rolled_back: bool = False
    security_gate: SecurityGate = "not-run"
    repository: str = ""
    workflow: str = ""
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.provider.strip() or not self.model.strip():
            raise ValueError("task_id, provider, and model are required")
        if self.attempts < 1:
            raise ValueError("attempts must be at least 1")
        if min(self.model_cost, self.tool_cost, self.human_review_minutes) < 0:
            raise ValueError("cost and review values cannot be negative")
        if min(self.elapsed_ms, self.input_tokens, self.output_tokens) < 0:
            raise ValueError("elapsed time and token counts cannot be negative")

    @property
    def verified_completion(self) -> bool:
        return self.verification_passed and self.artifacts_accepted and not self.rolled_back and self.security_gate != "block"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def receipt_metadata(self) -> dict[str, object]:
        """Return prompt-free numeric/enum metadata safe for a sanitized receipt."""
        return {
            "task_id": self.task_id,
            "provider": self.provider,
            "model": self.model,
            "attempts": self.attempts,
            "model_cost": self.model_cost,
            "tool_cost": self.tool_cost,
            "elapsed_ms": self.elapsed_ms,
            "human_review_minutes": self.human_review_minutes,
            "verification_passed": self.verification_passed,
            "artifacts_accepted": self.artifacts_accepted,
            "rolled_back": self.rolled_back,
            "security_gate": self.security_gate,
            "verified_completion": self.verified_completion,
            "repository": self.repository,
            "workflow": self.workflow,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


class TaskEconomicsWriter:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, record: TaskEconomics) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
        return self.path
