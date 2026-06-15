"""Monocle observability adapter.

Monocle is optional at runtime. This module imports it lazily only when tracing
is explicitly enabled, so Buddy Agent remains usable in environments where
`monocle_apptrace` is not installed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import import_module
from time import monotonic
from typing import Any, cast
from uuid import uuid4

from .sanitizer import Sanitizer


@dataclass(frozen=True)
class TraceSummary:
    """Public-safe summary of a private observability trace."""

    workflow: str
    status: str = "unknown"
    trace_ref: str = "private-or-redacted"
    duration_ms: int | None = None
    tool_categories: tuple[str, ...] = field(default_factory=tuple)
    assertions: tuple[str, ...] = field(default_factory=tuple)
    error_class: str | None = None
    raw_trace_exported: bool = False

    def as_receipt(self) -> Mapping[str, Any]:
        return {
            "provider": "monocle",
            "workflow": self.workflow,
            "status": self.status,
            "trace_ref": self.trace_ref,
            "duration_ms": self.duration_ms,
            "tool_categories": list(self.tool_categories),
            "assertions": list(self.assertions),
            "error_class": self.error_class,
            "raw_trace_exported": self.raw_trace_exported,
        }


class MonocleAdapter:
    """Optional wrapper around Monocle setup and trace receipt generation."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        workflow_name: str = "buddy-agent",
        sanitizer: Sanitizer | None = None,
    ) -> None:
        self.enabled = enabled
        self.workflow_name = workflow_name
        self.sanitizer = sanitizer or Sanitizer()
        self._setup_result: Mapping[str, Any] | None = None

    def setup(self) -> Mapping[str, Any]:
        """Set up Monocle telemetry if enabled and installed.

        Returns a public-safe status object instead of raising when Monocle is
        unavailable, because observability must not break Buddy runtime startup.
        """
        if not self.enabled:
            self._setup_result = {"enabled": False, "status": "disabled"}
            return self._setup_result

        try:
            module = import_module("monocle_apptrace")
            setup = cast(Callable[..., None], getattr(module, "setup_monocle_telemetry"))
            setup(workflow_name=self.workflow_name)
            self._setup_result = {"enabled": True, "status": "configured", "workflow": self.workflow_name}
        except Exception as exc:  # pragma: no cover - depends on optional package/runtime
            self._setup_result = {
                "enabled": True,
                "status": "unavailable",
                "workflow": self.workflow_name,
                "error_class": exc.__class__.__name__,
            }
        return self._setup_result

    def start_timer(self) -> tuple[str, float]:
        return f"trace-{uuid4().hex[:12]}", monotonic()

    def summarize(
        self,
        *,
        trace_ref: str,
        started_at: float | None = None,
        status: str = "completed",
        tool_categories: tuple[str, ...] = (),
        assertions: tuple[str, ...] = ("no_secrets_emitted", "no_raw_prompt_emitted"),
        error: BaseException | None = None,
    ) -> TraceSummary:
        duration_ms = int((monotonic() - started_at) * 1000) if started_at is not None else None
        error_class = error.__class__.__name__ if error else None
        if error:
            status = "failed"
        summary = TraceSummary(
            workflow=self.workflow_name,
            status=status,
            trace_ref=trace_ref,
            duration_ms=duration_ms,
            tool_categories=tuple(sorted(set(tool_categories))),
            assertions=assertions,
            error_class=error_class,
            raw_trace_exported=False,
        )
        safe_value, _ = self.sanitizer.sanitize(summary.as_receipt())
        safe = cast(Mapping[str, Any], safe_value)
        return TraceSummary(
            workflow=str(safe["workflow"]),
            status=str(safe["status"]),
            trace_ref=str(safe["trace_ref"]),
            duration_ms=cast(int | None, safe.get("duration_ms")),
            tool_categories=tuple(str(item) for item in safe.get("tool_categories") or ()),
            assertions=tuple(str(item) for item in safe.get("assertions") or ()),
            error_class=cast(str | None, safe.get("error_class")),
            raw_trace_exported=bool(safe.get("raw_trace_exported", False)),
        )
