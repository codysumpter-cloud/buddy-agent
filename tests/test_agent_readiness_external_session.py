import json

import pytest

from buddy_agent.agent_readiness.external_session import (
    ExternalAgentSession,
    ExternalSessionError,
)


def valid_payload():
    return {
        "schema": "buddy.external-agent-session.v1",
        "session_id": "session-123",
        "provider": "vscode",
        "harness": "codex",
        "status": "completed",
        "repository": "codysumpter-cloud/prismtek-apps",
        "worktree_ref": ".worktrees/session-123",
        "branch": "feat/example",
        "model": "gpt-example",
        "subagents": [
            {
                "span_id": "span-1",
                "parent_span_id": None,
                "provider": "codex",
                "model": "gpt-example",
                "status": "completed",
                "elapsed_ms": 1200,
                "tool_call_count": 1,
            }
        ],
        "tool_calls": [
            {
                "call_id": "call-1",
                "tool_name": "github.checks.read",
                "status": "completed",
                "elapsed_ms": 200,
                "resource_refs": ["pull/42/checks"],
                "argument_sha256": "a" * 64,
                "result_sha256": "b" * 64,
            }
        ],
        "commits": ["abcdef1234567890"],
        "pull_request_ref": "pull/42",
        "verification": [
            {
                "check": "ci",
                "status": "passed",
                "evidence_ref": "actions/runs/123",
                "observed_at": "2026-08-03T12:00:00Z",
            }
        ],
    }


def test_import_preserves_attribution_and_excludes_raw_payloads():
    session = ExternalAgentSession.from_dict(valid_payload())
    receipt = session.to_receipt().to_dict()
    assert receipt["status"] == "ok"
    metadata = receipt["metadata"]
    assert metadata["provider"] == "vscode"
    assert metadata["harness"] == "codex"
    assert metadata["worktree_ref"] == ".worktrees/session-123"
    assert metadata["commits"] == ["abcdef1234567890"]
    assert metadata["pull_request_ref"] == "pull/42"
    assert metadata["source_receipt_sha256"]
    assert metadata["raw_prompts"] == "excluded"
    assert metadata["raw_tool_payloads"] == "excluded"
    serialized = json.dumps(receipt)
    assert "github.checks.read" in serialized
    assert "source_receipt_sha256" in serialized


def test_completed_session_without_verification_requires_review():
    payload = valid_payload()
    payload["verification"] = []
    session = ExternalAgentSession.from_dict(payload)
    assert session.verification_complete is False
    assert session.to_receipt().status == "review"


def test_failed_verification_marks_receipt_error():
    payload = valid_payload()
    payload["verification"][0]["status"] = "failed"
    session = ExternalAgentSession.from_dict(payload)
    assert session.to_receipt().status == "error"


@pytest.mark.parametrize(
    "field,value",
    [
        ("worktree_ref", "/Users/prismtek/private-worktree"),
        ("worktree_ref", "C:\\Users\\prismtek\\private-worktree"),
        ("repository", "../other-repository"),
    ],
)
def test_absolute_or_escaping_host_references_are_rejected(field, value):
    payload = valid_payload()
    payload[field] = value
    with pytest.raises(ExternalSessionError, match="absolute host path|escape"):
        ExternalAgentSession.from_dict(payload)


@pytest.mark.parametrize(
    "forbidden",
    [
        {"prompt": "private instructions"},
        {"messages": [{"role": "user", "content": "private"}]},
        {"browser_state": {"cookies": []}},
        {"credentials": {"api_key": "private"}},
        {"tool_calls": [{"call_id": "x", "tool_name": "y", "raw_output": "private"}]},
    ],
)
def test_raw_or_sensitive_payload_fields_are_rejected(forbidden):
    payload = valid_payload()
    payload.update(forbidden)
    with pytest.raises(ExternalSessionError, match="forbidden raw or sensitive field"):
        ExternalAgentSession.from_dict(payload)


def test_duplicate_call_ids_and_invalid_commit_shas_are_rejected():
    duplicate = valid_payload()
    duplicate["tool_calls"].append(dict(duplicate["tool_calls"][0]))
    with pytest.raises(ExternalSessionError, match="tool call IDs"):
        ExternalAgentSession.from_dict(duplicate)

    invalid_commit = valid_payload()
    invalid_commit["commits"] = ["not-a-commit"]
    with pytest.raises(ExternalSessionError, match="hexadecimal SHAs"):
        ExternalAgentSession.from_dict(invalid_commit)


def test_source_receipt_hash_is_deterministic():
    first = ExternalAgentSession.from_dict(valid_payload())
    second = ExternalAgentSession.from_dict(valid_payload())
    assert first.source_receipt_sha256 == second.source_receipt_sha256
