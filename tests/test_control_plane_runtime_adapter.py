import json

import pytest

from buddy_agent.control_plane import (
    AgentRQClient,
    ControlPlaneRuntimeAdapter,
    KnowledgeVaultEmitter,
    MonocleAdapter,
    SanitizationError,
    Sanitizer,
)


class FakeTransport:
    def __init__(self):
        self.calls = []

    def call_tool(self, name, arguments=None):
        self.calls.append((name, arguments or {}))
        if name == "getNextTask":
            return {
                "id": "task-1",
                "title": "Wire runtime adapter",
                "status": "notstarted",
                "url": "https://workspace.mcp.agentrq.com/mcp?token=super-secret-token",
            }
        if name == "updateTaskStatus":
            return {"ok": True, "status": arguments["status"]}
        if name == "reply":
            return {"ok": True}
        if name == "getWorkspace":
            return {"name": "Buddy Runtime", "client_secret": "dont-emit-me"}
        return {"ok": True}


def test_runtime_adapter_completes_task_and_builds_sanitized_event():
    transport = FakeTransport()
    sanitizer = Sanitizer()
    client = AgentRQClient(transport, workspace_alias="buddy-runtime", sanitizer=sanitizer)
    adapter = ControlPlaneRuntimeAdapter(
        agentrq=client,
        monocle=MonocleAdapter(enabled=False, workflow_name="buddy-agent-test", sanitizer=sanitizer),
        knowledge_vault=KnowledgeVaultEmitter(sanitizer=sanitizer),
        sanitizer=sanitizer,
    )

    result = adapter.run_next_task(
        lambda task: {
            "changed_files": ["docs/CONTROL_PLANE_OBSERVABILITY.md"],
            "tool_categories": ["github", "runtime"],
            "secret": "sk-this-should-be-redacted-1234567890",
        }
    )

    assert result.status == "completed"
    assert result.event is not None
    assert result.event["source"] == "buddy-agent"
    assert result.event["event_type"] == "task_completed"

    serialized = json.dumps(result.event)
    assert "super-secret-token" not in serialized
    assert "sk-this-should-be-redacted" not in serialized
    assert "raw_trace_exported" in serialized
    assert "resourceSpans" not in serialized
    assert ("updateTaskStatus", {"taskId": "task-1", "status": "ongoing"}) in transport.calls
    assert ("updateTaskStatus", {"taskId": "task-1", "status": "completed"}) in transport.calls


def test_sanitizer_blocks_raw_trace_and_prompt_fields():
    sanitizer = Sanitizer()

    with pytest.raises(SanitizationError):
        sanitizer.assert_safe({"observability": {"trace": {"resourceSpans": []}}})

    with pytest.raises(SanitizationError):
        sanitizer.assert_safe({"messages": [{"role": "user", "content": "private raw chat"}]})


def test_attachment_download_is_deny_by_default():
    client = AgentRQClient(FakeTransport())

    with pytest.raises(PermissionError):
        client.download_attachment("attachment-1")


def test_approval_receipt_never_treats_silence_as_approval():
    client = AgentRQClient(FakeTransport())
    task = client.get_next_task()
    adapter = ControlPlaneRuntimeAdapter(agentrq=client)

    with pytest.raises(ValueError):
        adapter.approval_receipt(
            task=task,
            requested_action="run broad shell command",
            risk_class="repo-mutation",
            approval_outcome="silence",
        )

    receipt = adapter.approval_receipt(
        task=task,
        requested_action="run targeted validation",
        risk_class="repo-mutation",
        approval_outcome="denied",
    )
    assert receipt["approval_outcome"] == "denied"
