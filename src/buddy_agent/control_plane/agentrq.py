"""AgentRQ control-plane adapter.

This module does not store AgentRQ credentials and does not open network
connections by itself. Runtime callers inject a transport that knows how to call
AgentRQ MCP tools. That keeps `.mcp.json`, tokenized URLs, and OAuth material
local to the operator environment.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol, cast

from .sanitizer import Sanitizer


class ToolTransport(Protocol):
    """Minimal MCP/tool transport expected by the AgentRQ adapter."""

    def call_tool(self, name: str, arguments: Mapping[str, Any] | None = None) -> Any:
        """Call an allowlisted external tool and return its result."""


@dataclass(frozen=True)
class AgentRQTask:
    """Public-safe task shape used by Buddy Agent."""

    task_id: str
    title: str
    status: str = "notstarted"
    workspace_alias: str = "agentrq-workspace"
    assignee: str | None = None
    public_ref: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class AgentRQClient:
    """Small allowlisted adapter for AgentRQ MCP-style task operations."""

    allowed_statuses: ClassVar[frozenset[str]] = frozenset({"notstarted", "ongoing", "blocked", "completed"})
    allowed_tools: ClassVar[frozenset[str]] = frozenset({
        "getWorkspace",
        "getNextTask",
        "getTaskMessages",
        "reply",
        "updateTaskStatus",
        "downloadAttachment",
    })

    def __init__(
        self,
        transport: ToolTransport,
        *,
        workspace_alias: str = "agentrq-workspace",
        allow_attachments: bool = False,
        sanitizer: Sanitizer | None = None,
    ) -> None:
        self.transport = transport
        self.workspace_alias = workspace_alias
        self.allow_attachments = allow_attachments
        self.sanitizer = sanitizer or Sanitizer()

    def get_workspace(self) -> Mapping[str, Any]:
        result = self._call("getWorkspace", {})
        return self._safe_mapping(result)

    def get_next_task(self) -> AgentRQTask | None:
        result = self._call("getNextTask", {})
        if not result:
            return None
        safe = self._safe_mapping(result)
        task_id = str(safe.get("id") or safe.get("task_id") or safe.get("taskId") or "")
        title = str(safe.get("title") or safe.get("name") or "Untitled AgentRQ task")
        status = str(safe.get("status") or "notstarted")
        assignee = safe.get("assignee")
        public_ref = safe.get("public_ref") or safe.get("url") or safe.get("ref")
        metadata = {
            k: v
            for k, v in safe.items()
            if k
            not in {"id", "task_id", "taskId", "title", "name", "status", "assignee", "public_ref", "url", "ref"}
        }
        return AgentRQTask(
            task_id=task_id,
            title=title,
            status=status,
            workspace_alias=self.workspace_alias,
            assignee=str(assignee) if assignee is not None else None,
            public_ref=str(public_ref) if public_ref is not None else None,
            metadata=metadata,
        )

    def update_task_status(self, task_id: str, status: str) -> Mapping[str, Any]:
        if status not in self.allowed_statuses:
            raise ValueError(f"Unsupported AgentRQ task status: {status}")
        return self._safe_mapping(self._call("updateTaskStatus", {"taskId": task_id, "status": status}))

    def reply(self, task_id: str, message: str) -> Mapping[str, Any]:
        safe_payload_value, _ = self.sanitizer.sanitize({"taskId": task_id, "message": message})
        safe_payload = cast(Mapping[str, Any], safe_payload_value)
        return self._safe_mapping(self._call("reply", safe_payload))

    def get_task_messages(self, task_id: str) -> Mapping[str, Any]:
        # This may contain raw task chat. Return only sanitized output and let the
        # sanitizer block prompt/transcript-like fields before durable emission.
        return self._safe_mapping(self._call("getTaskMessages", {"taskId": task_id}))

    def download_attachment(self, attachment_id: str) -> Mapping[str, Any]:
        if not self.allow_attachments:
            raise PermissionError("AgentRQ attachment download is disabled by Buddy policy")
        return self._safe_mapping(self._call("downloadAttachment", {"attachmentId": attachment_id}))

    def task_receipt(
        self,
        task: AgentRQTask,
        *,
        approval_required: bool = False,
        approval_outcome: str = "not_required",
    ) -> Mapping[str, Any]:
        receipt = {
            "provider": "agentrq",
            "workspace_alias": self.workspace_alias,
            "task_id": task.task_id,
            "task_title": task.title,
            "task_status": task.status,
            "public_ref": task.public_ref,
            "approval_required": approval_required,
            "approval_outcome": approval_outcome,
        }
        safe, _ = self.sanitizer.sanitize(receipt)
        return cast(Mapping[str, Any], safe)

    def _call(self, tool_name: str, arguments: Mapping[str, Any] | None) -> Any:
        if tool_name not in self.allowed_tools:
            raise ValueError(f"Unsupported AgentRQ tool: {tool_name}")
        safe_arguments_value, _ = self.sanitizer.sanitize(dict(arguments or {}))
        safe_arguments = cast(Mapping[str, Any], safe_arguments_value)
        return self.transport.call_tool(tool_name, safe_arguments)

    def _safe_mapping(self, result: Any) -> Mapping[str, Any]:
        if isinstance(result, Mapping):
            safe, _ = self.sanitizer.sanitize(dict(result))
            return cast(Mapping[str, Any], safe)
        safe, _ = self.sanitizer.sanitize({"value": result})
        return cast(Mapping[str, Any], safe)
