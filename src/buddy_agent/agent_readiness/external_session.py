"""Sanitized ingestion for external agent execution sessions."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any, Literal, cast

from buddy_agent.receipts import JSONValue, ReceiptRecord, ReceiptStatus

SessionStatus = Literal["completed", "failed", "cancelled", "timed_out", "running"]
ToolCallStatus = Literal["completed", "failed", "cancelled", "timed_out", "rejected"]
VerificationStatus = Literal["passed", "failed", "pending", "not_run"]

_COMMIT = re.compile(r"^[0-9a-fA-F]{7,64}$")
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_FORBIDDEN_KEY = re.compile(
    r"(?:^|_)(?:prompt|messages?|raw|input|output|browser_state|cookie|credential|"
    r"password|secret|token|api_key|private_key|environment|env)(?:$|_)",
    re.IGNORECASE,
)


class ExternalSessionError(ValueError):
    """The external session cannot be retained safely or consistently."""


def _text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ExternalSessionError(f"{field} is required")
    if "\x00" in text:
        raise ExternalSessionError(f"{field} contains a NUL byte")
    return text


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _nonnegative_int(value: Any, field: str) -> int:
    number = int(value)
    if number < 0:
        raise ExternalSessionError(f"{field} cannot be negative")
    return number


def _safe_ref(value: Any, field: str) -> str | None:
    text = _optional_text(value, field)
    if text is None:
        return None
    if text.startswith(("/", "~")) or _WINDOWS_ABSOLUTE.match(text):
        raise ExternalSessionError(f"{field} must not contain an absolute host path")
    path = PurePosixPath(text.replace("\\", "/"))
    if ".." in path.parts:
        raise ExternalSessionError(f"{field} must not escape its logical namespace")
    return text


def _assert_no_raw_payloads(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if _FORBIDDEN_KEY.search(key_text):
                raise ExternalSessionError(f"forbidden raw or sensitive field at {path}.{key_text}")
            _assert_no_raw_payloads(child, f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _assert_no_raw_payloads(child, f"{path}[{index}]")


def _hash_payload(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class AgentSpan:
    span_id: str
    parent_span_id: str | None
    provider: str
    model: str | None
    status: SessionStatus
    elapsed_ms: int
    tool_call_count: int

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AgentSpan:
        status = str(payload.get("status", "completed"))
        if status not in {"completed", "failed", "cancelled", "timed_out", "running"}:
            raise ExternalSessionError(f"unsupported agent span status: {status}")
        return cls(
            span_id=_text(payload.get("span_id"), "subagents[].span_id"),
            parent_span_id=_optional_text(
                payload.get("parent_span_id"), "subagents[].parent_span_id"
            ),
            provider=_text(payload.get("provider"), "subagents[].provider"),
            model=_optional_text(payload.get("model"), "subagents[].model"),
            status=cast(SessionStatus, status),
            elapsed_ms=_nonnegative_int(payload.get("elapsed_ms", 0), "subagents[].elapsed_ms"),
            tool_call_count=_nonnegative_int(
                payload.get("tool_call_count", 0), "subagents[].tool_call_count"
            ),
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return cast(dict[str, JSONValue], asdict(self))


@dataclass(frozen=True)
class ExternalToolReceipt:
    call_id: str
    tool_name: str
    status: ToolCallStatus
    elapsed_ms: int
    resource_refs: tuple[str, ...] = ()
    argument_sha256: str | None = None
    result_sha256: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ExternalToolReceipt:
        status = str(payload.get("status", "completed"))
        if status not in {"completed", "failed", "cancelled", "timed_out", "rejected"}:
            raise ExternalSessionError(f"unsupported tool call status: {status}")
        argument_hash = _optional_text(
            payload.get("argument_sha256"), "tool_calls[].argument_sha256"
        )
        result_hash = _optional_text(
            payload.get("result_sha256"), "tool_calls[].result_sha256"
        )
        for field, value in (
            ("argument_sha256", argument_hash),
            ("result_sha256", result_hash),
        ):
            if value is not None and not _SHA256.fullmatch(value):
                raise ExternalSessionError(f"tool_calls[].{field} must be a SHA-256 hex digest")
        refs_raw = payload.get("resource_refs", [])
        if not isinstance(refs_raw, Sequence) or isinstance(refs_raw, (str, bytes, bytearray)):
            raise ExternalSessionError("tool_calls[].resource_refs must be an array")
        refs = tuple(
            _safe_ref(item, "tool_calls[].resource_refs[]") or "" for item in refs_raw
        )
        if len(set(refs)) != len(refs):
            raise ExternalSessionError("tool_calls[].resource_refs must be unique")
        return cls(
            call_id=_text(payload.get("call_id"), "tool_calls[].call_id"),
            tool_name=_text(payload.get("tool_name"), "tool_calls[].tool_name"),
            status=cast(ToolCallStatus, status),
            elapsed_ms=_nonnegative_int(payload.get("elapsed_ms", 0), "tool_calls[].elapsed_ms"),
            resource_refs=refs,
            argument_sha256=argument_hash,
            result_sha256=result_hash,
        )

    def to_dict(self) -> dict[str, JSONValue]:
        value = cast(dict[str, JSONValue], asdict(self))
        value["resource_refs"] = list(self.resource_refs)
        return value


@dataclass(frozen=True)
class VerificationEvidence:
    check: str
    status: VerificationStatus
    evidence_ref: str
    observed_at: str | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> VerificationEvidence:
        status = str(payload.get("status", "not_run"))
        if status not in {"passed", "failed", "pending", "not_run"}:
            raise ExternalSessionError(f"unsupported verification status: {status}")
        return cls(
            check=_text(payload.get("check"), "verification[].check"),
            status=cast(VerificationStatus, status),
            evidence_ref=_safe_ref(
                payload.get("evidence_ref"), "verification[].evidence_ref"
            )
            or "",
            observed_at=_optional_text(
                payload.get("observed_at"), "verification[].observed_at"
            ),
        )

    def to_dict(self) -> dict[str, JSONValue]:
        return cast(dict[str, JSONValue], asdict(self))


@dataclass(frozen=True)
class ExternalAgentSession:
    schema: str
    session_id: str
    provider: str
    harness: str
    status: SessionStatus
    repository: str | None
    worktree_ref: str | None
    branch: str | None
    model: str | None
    subagents: tuple[AgentSpan, ...]
    tool_calls: tuple[ExternalToolReceipt, ...]
    commits: tuple[str, ...]
    pull_request_ref: str | None
    verification: tuple[VerificationEvidence, ...]
    source_receipt_sha256: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ExternalAgentSession:
        _assert_no_raw_payloads(payload)
        schema = str(payload.get("schema", "buddy.external-agent-session.v1"))
        if schema != "buddy.external-agent-session.v1":
            raise ExternalSessionError(f"unsupported external session schema: {schema}")
        status = str(payload.get("status", "completed"))
        if status not in {"completed", "failed", "cancelled", "timed_out", "running"}:
            raise ExternalSessionError(f"unsupported session status: {status}")

        subagents_raw = payload.get("subagents", [])
        tool_calls_raw = payload.get("tool_calls", [])
        commits_raw = payload.get("commits", [])
        verification_raw = payload.get("verification", [])
        for field, value in (
            ("subagents", subagents_raw),
            ("tool_calls", tool_calls_raw),
            ("commits", commits_raw),
            ("verification", verification_raw),
        ):
            if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
                raise ExternalSessionError(f"{field} must be an array")

        commits = tuple(_text(value, "commits[]") for value in commits_raw)
        if any(not _COMMIT.fullmatch(commit) for commit in commits):
            raise ExternalSessionError("commits[] must contain 7-64 character hexadecimal SHAs")
        if len(set(commits)) != len(commits):
            raise ExternalSessionError("commits[] must be unique")

        subagents = tuple(
            AgentSpan.from_dict(cast(Mapping[str, Any], item)) for item in subagents_raw
        )
        if len({span.span_id for span in subagents}) != len(subagents):
            raise ExternalSessionError("subagent span IDs must be unique")
        tool_calls = tuple(
            ExternalToolReceipt.from_dict(cast(Mapping[str, Any], item))
            for item in tool_calls_raw
        )
        if len({call.call_id for call in tool_calls}) != len(tool_calls):
            raise ExternalSessionError("tool call IDs must be unique")
        verification = tuple(
            VerificationEvidence.from_dict(cast(Mapping[str, Any], item))
            for item in verification_raw
        )

        return cls(
            schema=schema,
            session_id=_text(payload.get("session_id"), "session_id"),
            provider=_text(payload.get("provider"), "provider"),
            harness=_text(payload.get("harness"), "harness"),
            status=cast(SessionStatus, status),
            repository=_safe_ref(payload.get("repository"), "repository"),
            worktree_ref=_safe_ref(payload.get("worktree_ref"), "worktree_ref"),
            branch=_safe_ref(payload.get("branch"), "branch"),
            model=_optional_text(payload.get("model"), "model"),
            subagents=subagents,
            tool_calls=tool_calls,
            commits=commits,
            pull_request_ref=_safe_ref(
                payload.get("pull_request_ref"), "pull_request_ref"
            ),
            verification=verification,
            source_receipt_sha256=_hash_payload(payload),
        )

    @property
    def verification_complete(self) -> bool:
        return bool(self.verification) and all(
            item.status == "passed" for item in self.verification
        )

    @property
    def receipt_status(self) -> ReceiptStatus:
        if self.status == "failed" or any(
            item.status == "failed" for item in self.verification
        ):
            return "error"
        if self.status in {"cancelled", "timed_out"}:
            return "review"
        if self.status == "completed" and self.verification_complete:
            return "ok"
        return "review"

    def to_receipt(self) -> ReceiptRecord:
        metadata: dict[str, JSONValue] = {
            "schema": self.schema,
            "session_id": self.session_id,
            "provider": self.provider,
            "harness": self.harness,
            "session_status": self.status,
            "repository": self.repository,
            "worktree_ref": self.worktree_ref,
            "branch": self.branch,
            "model": self.model,
            "subagents": [span.to_dict() for span in self.subagents],
            "tool_calls": [call.to_dict() for call in self.tool_calls],
            "commits": list(self.commits),
            "pull_request_ref": self.pull_request_ref,
            "verification": [item.to_dict() for item in self.verification],
            "verification_complete": self.verification_complete,
            "source_receipt_sha256": self.source_receipt_sha256,
            "raw_prompts": "excluded",
            "raw_tool_payloads": "excluded",
            "browser_state": "excluded",
            "credentials": "excluded",
        }
        return ReceiptRecord(
            action="external-agent-session-import",
            status=self.receipt_status,
            summary=(
                f"Imported {self.provider}/{self.harness} session {self.session_id} "
                f"with {len(self.tool_calls)} tool calls and "
                f"{len(self.verification)} verification records."
            ),
            metadata=metadata,
        )


def parse_external_session_json(text: str) -> ExternalAgentSession:
    payload = json.loads(text)
    if not isinstance(payload, Mapping):
        raise ExternalSessionError("external session document must be a JSON object")
    return ExternalAgentSession.from_dict(cast(Mapping[str, Any], payload))
