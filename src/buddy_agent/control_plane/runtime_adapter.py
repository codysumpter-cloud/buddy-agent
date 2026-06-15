"""High-level Buddy Agent runtime adapter for AgentRQ + Monocle + Knowledge Vault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .agentrq import AgentRQClient, AgentRQTask
from .knowledge_vault import KnowledgeVaultEmitter
from .monocle import MonocleAdapter, TraceSummary
from .sanitizer import Sanitizer

TaskRunner = Callable[[AgentRQTask], Mapping[str, Any] | None]


@dataclass(frozen=True)
class RuntimeAdapterResult:
    """Result from one control-plane task execution."""

    task: AgentRQTask | None
    status: str
    receipt: Mapping[str, Any] | None
    event: Mapping[str, Any] | None
    trace: TraceSummary | None


class ControlPlaneRuntimeAdapter:
    """Coordinate AgentRQ task state, Monocle summary, and KV receipts.

    This is the first live adapter layer. It can be called by an existing Buddy
    runtime loop without changing shell/tool approval policy. The external
    AgentRQ connection is injected, Monocle is opt-in, and Knowledge Vault output
    is schema-shaped sanitized event data.
    """

    def __init__(
        self,
        *,
        agentrq: AgentRQClient | None = None,
        monocle: MonocleAdapter | None = None,
        knowledge_vault: KnowledgeVaultEmitter | None = None,
        sanitizer: Sanitizer | None = None,
    ) -> None:
        self.sanitizer = sanitizer or Sanitizer()
        self.agentrq = agentrq
        self.monocle = monocle or MonocleAdapter(enabled=False, sanitizer=self.sanitizer)
        self.knowledge_vault = knowledge_vault or KnowledgeVaultEmitter(sanitizer=self.sanitizer)

    def run_next_task(
        self,
        runner: TaskRunner,
        *,
        complete_on_success: bool = True,
    ) -> RuntimeAdapterResult:
        if self.agentrq is None:
            raise RuntimeError("AgentRQ client is not configured")

        self.monocle.setup()
        task = self.agentrq.get_next_task()
        if task is None:
            return RuntimeAdapterResult(task=None, status="idle", receipt=None, event=None, trace=None)

        trace_ref, started_at = self.monocle.start_timer()
        self.agentrq.update_task_status(task.task_id, "ongoing")

        try:
            runner_result = runner(task) or {}
            safe_runner_result, _ = self.sanitizer.sanitize(runner_result)
            final_status = "completed" if complete_on_success else task.status
            if complete_on_success:
                self.agentrq.update_task_status(task.task_id, "completed")
            trace = self.monocle.summarize(
                trace_ref=trace_ref,
                started_at=started_at,
                status="completed",
                tool_categories=tuple(safe_runner_result.get("tool_categories") or ("runtime",)),
                assertions=("no_secrets_emitted", "no_raw_prompt_emitted", "validation_completed"),
            )
            receipt = self._build_receipt(task, final_status=final_status, runner_result=safe_runner_result, trace=trace)
            event = self.knowledge_vault.build_event(
                event_class="task",
                title=f"Completed AgentRQ task: {task.title}",
                summary="Buddy Agent completed a control-plane task and produced a sanitized runtime receipt.",
                payload=receipt,
                event_type="task_completed",
            )
            return RuntimeAdapterResult(task=task, status=final_status, receipt=receipt, event=event, trace=trace)
        except Exception as exc:
            self.agentrq.update_task_status(task.task_id, "blocked")
            trace = self.monocle.summarize(
                trace_ref=trace_ref,
                started_at=started_at,
                status="failed",
                tool_categories=("runtime",),
                assertions=("no_secrets_emitted", "no_raw_prompt_emitted", "blocked_on_error"),
                error=exc,
            )
            receipt = self._build_receipt(
                task,
                final_status="blocked",
                runner_result={"error_class": exc.__class__.__name__},
                trace=trace,
            )
            event = self.knowledge_vault.build_event(
                event_class="system",
                title=f"Blocked AgentRQ task: {task.title}",
                summary="Buddy Agent blocked a control-plane task after a runtime error and produced a sanitized receipt.",
                payload=receipt,
                event_type="repo_updated",
            )
            return RuntimeAdapterResult(task=task, status="blocked", receipt=receipt, event=event, trace=trace)

    def approval_receipt(
        self,
        *,
        task: AgentRQTask,
        requested_action: str,
        risk_class: str,
        approval_outcome: str,
    ) -> Mapping[str, Any]:
        if approval_outcome not in {"approved", "denied", "needs_more_context", "expired", "not_required"}:
            raise ValueError(f"Unsupported approval outcome: {approval_outcome}")
        receipt = {
            "control_plane": self.agentrq.task_receipt(task, approval_required=True, approval_outcome=approval_outcome) if self.agentrq else {},
            "requested_action": requested_action,
            "risk_class": risk_class,
            "approval_required": True,
            "approval_outcome": approval_outcome,
        }
        safe, _ = self.sanitizer.sanitize(receipt)
        return safe

    def _build_receipt(
        self,
        task: AgentRQTask,
        *,
        final_status: str,
        runner_result: Mapping[str, Any],
        trace: TraceSummary,
    ) -> Mapping[str, Any]:
        control_plane = self.agentrq.task_receipt(task, approval_required=False, approval_outcome="not_required") if self.agentrq else {}
        receipt = {
            "control_plane": {**control_plane, "task_status": final_status},
            "observability": trace.as_receipt(),
            "runtime": {
                "runner_status": final_status,
                "result": runner_result,
            },
            "redaction": {
                "raw_prompts": "excluded",
                "raw_traces": "excluded",
                "secrets": "excluded",
                "private_paths": "redacted",
            },
        }
        safe, _ = self.sanitizer.sanitize(receipt)
        return safe
