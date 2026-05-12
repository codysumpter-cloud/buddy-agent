"""Small scheduler primitives for Buddy Agent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

AutomationHandler = Callable[[], str]


@dataclass(frozen=True)
class AutomationJob:
    """A scheduled job definition."""

    name: str
    description: str
    schedule: str
    handler: AutomationHandler


@dataclass(frozen=True)
class AutomationRun:
    """Result of running a scheduled job."""

    job_name: str
    started_at: datetime
    output: str


class AutomationRegistry:
    """Registry for scheduled jobs.

    The scaffold does not include a clock loop yet. It only records jobs and lets tests or
    command handlers run them directly.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, AutomationJob] = {}

    def register(self, job: AutomationJob) -> None:
        """Register a scheduled job."""
        if job.name in self._jobs:
            raise ValueError(f"Automation already registered: {job.name}")
        self._jobs[job.name] = job

    def names(self) -> tuple[str, ...]:
        """Return job names in stable order."""
        return tuple(sorted(self._jobs))

    def run_now(self, name: str) -> AutomationRun:
        """Run a registered job immediately."""
        job = self._jobs[name]
        return AutomationRun(job_name=job.name, started_at=datetime.now(UTC), output=job.handler())
