"""Optional MCP task lifecycle emission into a configured KnowledgeVault inbox."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from buddy_agent.receipts.record import JSONValue
from buddy_agent.tasks.events import KnowledgeVaultTaskEventSink, TaskEventResult
from buddy_agent.tasks.models import TaskRecord, TaskStatus
from buddy_agent.tasks.store import TaskStoreError

from . import mcp_server as base
from . import mcp_tasks

MutationHandler = Callable[[base.BuddyMcpConfig, dict[str, Any]], dict[str, Any]]

TOOL_ACTIONS = {
    "buddy.task.create": "buddy.task.create",
    "buddy.task.plan": "buddy.task.plan",
    "buddy.task.approval": "buddy.task.approval",
    "buddy.task.start": "buddy.task.start",
    "buddy.task.step": "buddy.task.step",
    "buddy.task.complete": "buddy.task.complete",
    "buddy.task.cancel": "buddy.task.cancel",
    "buddy.task.resume": "buddy.task.resume",
}

TOOL_SUMMARIES = {
    "buddy.task.create": "Buddy task created",
    "buddy.task.plan": "Buddy task plan updated",
    "buddy.task.approval": "Buddy task approval decided",
    "buddy.task.start": "Buddy task started",
    "buddy.task.step": "Buddy task step updated",
    "buddy.task.complete": "Buddy task completed",
    "buddy.task.cancel": "Buddy task cancelled",
    "buddy.task.resume": "Buddy task resumed",
}

_WRAPPED = False


def _inbox() -> Path | None:
    configured = os.getenv("BUDDY_VAULT_INBOX", "").strip()
    return Path(configured).expanduser().resolve() if configured else None


def _previous_status(
    name: str,
    config: base.BuddyMcpConfig,
    arguments: dict[str, Any],
) -> TaskStatus | None:
    if name == "buddy.task.create":
        return None
    task_id = arguments.get("task_id")
    if not isinstance(task_id, str):
        return None
    try:
        return mcp_tasks._runtime(config).store.load(task_id).status
    except TaskStoreError:
        return None


def _result_task(result: dict[str, Any]) -> TaskRecord:
    return TaskRecord.from_dict(cast(dict[str, JSONValue], result))


def _wrap(name: str, handler: MutationHandler) -> MutationHandler:
    def wrapped(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
        previous = _previous_status(name, config, arguments)
        result = handler(config, arguments)
        inbox = _inbox()
        if inbox is None:
            event_result = TaskEventResult(configured=False, emitted=False)
        else:
            event_result = KnowledgeVaultTaskEventSink(inbox).emit(
                action=TOOL_ACTIONS[name],
                previous_status=previous,
                task=_result_task(result),
                summary=TOOL_SUMMARIES[name],
            )
        return {**result, "memory_event": event_result.to_dict()}

    return wrapped


def register_task_event_hooks() -> None:
    """Wrap mutating task tools exactly once after task tools are registered."""
    global _WRAPPED
    if _WRAPPED:
        return
    handlers = cast(dict[str, MutationHandler], base.TOOL_HANDLERS)
    for name in TOOL_ACTIONS:
        handler = handlers.get(name)
        if handler is None:
            raise RuntimeError(f"task MCP tool is not registered: {name}")
        handlers[name] = _wrap(name, handler)
    _WRAPPED = True
