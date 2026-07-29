"""End-to-end Trust Fabric evaluation and verification pipeline."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import RetrievalEnvelope
from .normalizer import normalize_retrieval
from .policy import evaluate_policy


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source_summary(envelope: RetrievalEnvelope) -> list[dict[str, Any]]:
    return [source.public_dict(include_excerpt=False) for source in envelope.sources]


def _report(envelope: RetrievalEnvelope, decision: dict[str, Any]) -> str:
    lines = [
        "# Prismtek Trust Fabric provenance report",
        "",
        f"- Task: `{envelope.task_id}`",
        f"- Retrieval provider: `{envelope.provider}`",
        f"- Agent: `{envelope.agent_id}`",
        f"- Risk: `{envelope.risk_level}`",
        f"- Decision: **{decision['decision'].upper()}**",
        f"- Query digest: `{envelope.query_digest}`",
        "",
        "## Evidence",
        "",
        "| Source | Type | Trust | Confidence | Observed | Valid until | Hash |",
        "|---|---|---|---:|---|---|---|",
    ]
    for source in envelope.sources:
        lines.append(
            f"| `{source.source_id}` | {source.source_type} | {source.trust_tier} | "
            f"{source.confidence:.2f} | {source.observed_at or 'unknown'} | "
            f"{source.valid_until or 'unspecified'} | `{source.content_hash}` |"
        )
    if not envelope.sources:
        lines.append("| _none_ | | | | | | |")
    lines.extend(["", "## Decision reasons", ""])
    lines.extend(f"- {reason}" for reason in decision["reasons"])
    if decision["required_actions"]:
        lines.extend(["", "## Required actions", ""])
        lines.extend(f"- {action}" for action in decision["required_actions"])
    lines.extend(
        [
            "",
            "Raw prompts, credentials, browser state, and source excerpts are intentionally excluded from this report.",
            "",
        ]
    )
    return "\n".join(lines)


def evaluate_retrieval(
    payload: dict[str, Any], output_dir: str | Path, *, as_of: str | None = None
) -> dict[str, Any]:
    out = Path(output_dir)
    envelope = normalize_retrieval(payload)
    decision_obj = evaluate_policy(envelope, as_of=as_of)
    decision = {
        "schema_version": "1.0",
        "task_id": envelope.task_id,
        "evaluated_at": _now(),
        "risk_level": envelope.risk_level,
        **decision_obj.as_dict(),
    }
    evidence = {
        "schema_version": "1.0",
        "task_id": envelope.task_id,
        "provider": envelope.provider,
        "agent_id": envelope.agent_id,
        "retrieved_at": envelope.retrieved_at,
        "query_digest": envelope.query_digest,
        "sources": _source_summary(envelope),
    }
    receipt = {
        "schema_version": "1.0",
        "task_id": envelope.task_id,
        "claim": "Retrieved evidence is admissible for guarded execution.",
        "status": "source_backed" if decision["decision"] == "allow" else "blocked",
        "decision": decision["decision"],
        "verified": False,
        "artifact_accepted": False,
        "security_gate": "not-run",
        "evidence_refs": [source["content_hash"] for source in evidence["sources"]],
        "checked_at": decision["evaluated_at"],
    }
    event = {
        "event_id": f"evt-trust-{envelope.task_id}",
        "event_type": "evidence_evaluated",
        "source": "buddy-agent",
        "timestamp": decision["evaluated_at"],
        "payload": {
            "task_id": envelope.task_id,
            "provider": envelope.provider,
            "risk_level": envelope.risk_level,
            "decision": decision["decision"],
            "query_digest": envelope.query_digest,
            "evidence_hashes": receipt["evidence_refs"],
            "stale_source_ids": decision["stale_source_ids"],
            "conflicting_source_ids": decision["conflicting_source_ids"],
        },
    }
    _write(out / "evidence-bundle.json", evidence)
    _write(out / "policy-decision.json", decision)
    _write(out / "execution-receipt.json", receipt)
    _write(out / "memory-event.json", event)
    (out / "provenance-report.md").write_text(_report(envelope, decision), encoding="utf-8")
    return {"evidence": evidence, "decision": decision, "receipt": receipt, "event": event}


def finalize_run(
    output_dir: str | Path,
    artifact: str | Path,
    *,
    reviewer: str,
    review_approved: bool = False,
    security_gate: str = "pass",
    provider: str = "unknown",
    model: str = "unknown",
    attempts: int = 1,
    model_cost: float = 0.0,
    tool_cost: float = 0.0,
    elapsed_ms: int = 0,
    human_review_minutes: float = 0.0,
) -> dict[str, Any]:
    out = Path(output_dir)
    decision = json.loads((out / "policy-decision.json").read_text(encoding="utf-8"))
    if decision["decision"] == "block":
        raise ValueError("blocked evidence cannot be finalized")
    if decision["decision"] == "review" and not review_approved:
        raise ValueError("review decision requires explicit review approval")
    if security_gate != "pass":
        raise ValueError("security gate must pass before finalization")
    artifact_path = Path(artifact)
    if not artifact_path.is_file():
        raise ValueError(f"artifact does not exist: {artifact_path}")
    artifact_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"
    checked_at = _now()
    receipt = json.loads((out / "execution-receipt.json").read_text(encoding="utf-8"))
    receipt.update(
        {
            "status": "verified",
            "verified": True,
            "artifact_accepted": True,
            "artifact": {"path": str(artifact_path), "sha256": artifact_hash},
            "reviewer": reviewer,
            "review_approved": bool(review_approved or decision["decision"] == "allow"),
            "security_gate": security_gate,
            "checked_at": checked_at,
        }
    )
    event = {
        "event_id": f"evt-verified-{decision['task_id']}",
        "event_type": "execution_verified",
        "source": "buddy-agent",
        "timestamp": checked_at,
        "payload": {
            "task_id": decision["task_id"],
            "decision": decision["decision"],
            "artifact_hash": artifact_hash,
            "reviewer": reviewer,
            "security_gate": security_gate,
        },
    }
    economics = {
        "task_id": decision["task_id"],
        "provider": provider,
        "model": model,
        "attempts": attempts,
        "model_cost": model_cost,
        "tool_cost": tool_cost,
        "elapsed_ms": elapsed_ms,
        "human_review_minutes": human_review_minutes,
        "verification_passed": True,
        "artifacts_accepted": True,
        "rolled_back": False,
        "security_gate": security_gate,
        "repository": "codysumpter-cloud/buddy-agent",
        "workflow": "prismtek-trust-fabric",
    }
    _write(out / "execution-receipt.json", receipt)
    _write(out / "memory-event.json", event)
    _write(out / "task-economics.json", economics)
    return {"receipt": receipt, "event": event, "economics": economics}
