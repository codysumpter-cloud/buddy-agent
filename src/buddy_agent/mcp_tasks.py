"""MCP extension tools for the persistent Buddy task lifecycle."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

from buddy_agent.receipts import ReceiptWriter
from buddy_agent.tasks import TaskRisk, TaskRuntime, TaskStore, TaskStoreError, TaskTransitionError

from . import mcp_server as base

TASK_TOOLS = (
    base.ToolDefinition(
        "buddy.task.create",
        "Create a persistent Buddy task without inventing a plan or executing work.",
        {
            "type": "object",
            "properties": {
                "objective": {"type": "string", "minLength": 1, "maxLength": 12000},
                "risk": {
                    "type": "string",
                    "enum": ["read-only", "draft-only", "write", "repo-mutation", "destructive"],
                },
            },
            "required": ["objective"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.list",
        "List persistent Buddy tasks newest-first.",
        {"type": "object", "properties": {}, "additionalProperties": False},
    ),
    base.ToolDefinition(
        "buddy.task.get",
        "Read one persistent Buddy task by ID.",
        {
            "type": "object",
            "properties": {"task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"}},
            "required": ["task_id"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.plan",
        "Attach a reviewable plan and request human approval when the task risk requires it.",
        {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"},
                "steps": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": 1000},
                    "minItems": 1,
                    "maxItems": 30,
                },
                "verification": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": 500},
                    "maxItems": 30,
                },
            },
            "required": ["task_id", "steps"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.approval",
        "Approve or deny a pending Buddy task with an attributable human decision.",
        {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"},
                "approved": {"type": "boolean"},
                "decided_by": {"type": "string", "minLength": 1, "maxLength": 200},
                "note": {"type": "string", "maxLength": 2000},
            },
            "required": ["task_id", "approved", "decided_by"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.start",
        "Mark an approved/planned Buddy task running. This does not execute commands.",
        {
            "type": "object",
            "properties": {"task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"}},
            "required": ["task_id"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.step",
        "Record one running task step as completed or failed, with optional artifact references.",
        {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"},
                "step_id": {"type": "string", "pattern": "^step-[0-9]+$"},
                "completed": {"type": "boolean"},
                "detail": {"type": "string", "maxLength": 4000},
                "artifact_paths": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1, "maxLength": 1000},
                    "maxItems": 30,
                },
            },
            "required": ["task_id", "step_id", "completed"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.complete",
        "Complete a running task only after every planned step and required evidence reference is recorded.",
        {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"},
                "summary": {"type": "string", "minLength": 1, "maxLength": 4000},
            },
            "required": ["task_id", "summary"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.cancel",
        "Cancel a non-terminal Buddy task without executing external actions.",
        {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"},
                "reason": {"type": "string", "maxLength": 2000},
            },
            "required": ["task_id"],
            "additionalProperties": False,
        },
    ),
    base.ToolDefinition(
        "buddy.task.resume",
        "Resume a cancelled or failed Buddy task, preserving its identity and re-requesting approval when needed.",
        {
            "type": "object",
            "properties": {"task_id": {"type": "string", "pattern": "^task-[a-f0-9]{24}$"}},
            "required": ["task_id"],
            "additionalProperties": False,
        },
    ),
)


def _tasks_directory(config: base.BuddyMcpConfig) -> Path:
    configured = os.getenv("BUDDY_TASKS_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (config.project_root / ".buddy" / "runtime" / "tasks").resolve()


def _receipts_directory(config: base.BuddyMcpConfig) -> Path:
    configured = os.getenv("BUDDY_RECEIPTS_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (config.project_root / ".buddy" / "runtime" / "receipts").resolve()


def _runtime(config: base.BuddyMcpConfig) -> TaskRuntime:
    return TaskRuntime(
        TaskStore(_tasks_directory(config)),
        ReceiptWriter(_receipts_directory(config)),
    )


def _strings(arguments: dict[str, Any], key: str) -> list[str]:
    raw = arguments.get(key, [])
    if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
        raise base.McpToolError(f"{key} must be an array of strings")
    return [item for item in raw]


def _task_id(arguments: dict[str, Any]) -> str:
    value = arguments.get("task_id")
    if not isinstance(value, str) or not value:
        raise base.McpToolError("task_id is required")
    return value


def _safe_call(callback: Any) -> dict[str, Any]:
    try:
        result = callback()
    except (TaskStoreError, TaskTransitionError) as error:
        raise base.McpToolError(str(error)) from error
    return cast(dict[str, Any], result.to_dict())


def _create(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    objective = arguments.get("objective")
    if not isinstance(objective, str):
        raise base.McpToolError("objective is required")
    risk = arguments.get("risk", "read-only")
    if risk not in {"read-only", "draft-only", "write", "repo-mutation", "destructive"}:
        raise base.McpToolError("unsupported task risk")
    return _safe_call(
        lambda: _runtime(config).create(
            objective,
            risk=cast(TaskRisk, risk),
            project_root=config.project_root,
        )
    )


def _list(config: base.BuddyMcpConfig, _arguments: dict[str, Any]) -> dict[str, Any]:
    tasks = _runtime(config).store.list()
    return {"tasks": [task.to_dict() for task in tasks], "count": len(tasks)}


def _get(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    return _safe_call(lambda: _runtime(config).store.load(_task_id(arguments)))


def _plan(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    steps = _strings(arguments, "steps")
    verification = _strings(arguments, "verification")
    return _safe_call(
        lambda: _runtime(config).plan(
            _task_id(arguments),
            steps,
            verification=verification,
        )
    )


def _approval(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    approved = arguments.get("approved")
    decided_by = arguments.get("decided_by")
    note = arguments.get("note")
    if not isinstance(approved, bool):
        raise base.McpToolError("approved must be a boolean")
    if not isinstance(decided_by, str) or not decided_by.strip():
        raise base.McpToolError("decided_by is required")
    if note is not None and not isinstance(note, str):
        raise base.McpToolError("note must be a string")
    return _safe_call(
        lambda: _runtime(config).respond_approval(
            _task_id(arguments),
            approved=approved,
            decided_by=decided_by,
            note=note,
        )
    )


def _start(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    return _safe_call(lambda: _runtime(config).start(_task_id(arguments)))


def _step(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    step_id = arguments.get("step_id")
    completed = arguments.get("completed")
    detail = arguments.get("detail")
    if not isinstance(step_id, str) or not step_id:
        raise base.McpToolError("step_id is required")
    if not isinstance(completed, bool):
        raise base.McpToolError("completed must be a boolean")
    if detail is not None and not isinstance(detail, str):
        raise base.McpToolError("detail must be a string")
    return _safe_call(
        lambda: _runtime(config).update_step(
            _task_id(arguments),
            step_id,
            completed=completed,
            detail=detail,
            artifact_paths=_strings(arguments, "artifact_paths"),
        )
    )


def _complete(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    summary = arguments.get("summary")
    if not isinstance(summary, str):
        raise base.McpToolError("summary is required")
    return _safe_call(lambda: _runtime(config).complete(_task_id(arguments), summary))


def _cancel(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    reason = arguments.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise base.McpToolError("reason must be a string")
    return _safe_call(lambda: _runtime(config).cancel(_task_id(arguments), reason))


def _resume(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    return _safe_call(lambda: _runtime(config).resume(_task_id(arguments)))


TASK_HANDLERS = {
    "buddy.task.create": _create,
    "buddy.task.list": _list,
    "buddy.task.get": _get,
    "buddy.task.plan": _plan,
    "buddy.task.approval": _approval,
    "buddy.task.start": _start,
    "buddy.task.step": _step,
    "buddy.task.complete": _complete,
    "buddy.task.cancel": _cancel,
    "buddy.task.resume": _resume,
}


def register_task_tools() -> None:
    """Extend the core MCP registry exactly once."""
    additions = tuple(tool for tool in TASK_TOOLS if tool.name not in base.TOOL_BY_NAME)
    if not additions:
        return
    setattr(base, "TOOLS", (*base.TOOLS, *additions))
    base.TOOL_BY_NAME.update({tool.name: tool for tool in additions})
    base.TOOL_HANDLERS.update(TASK_HANDLERS)
