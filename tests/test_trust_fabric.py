from __future__ import annotations

from pathlib import Path

import pytest

from buddy_agent.trust_fabric.normalizer import normalize_retrieval
from buddy_agent.trust_fabric.pipeline import evaluate_retrieval, finalize_run

AS_OF = "2026-07-29T12:00:00Z"


def source(**overrides):
    payload = {
        "universalId": "src-1",
        "excerpt": "A source-backed fact.",
        "sourceType": "document",
        "observedAt": "2026-07-29T10:00:00Z",
        "validUntil": "2026-08-29T10:00:00Z",
        "confidence": 0.9,
        "trustTier": "verified",
    }
    payload.update(overrides)
    return payload


def envelope(**overrides):
    payload = {
        "provider": "mitosis-cortex",
        "query": "What should the agent do?",
        "agentId": "buddy",
        "taskId": "demo-1",
        "riskLevel": "medium",
        "sources": [source()],
    }
    payload.update(overrides)
    return payload


def test_normalizes_mitosis_shaped_fields():
    normalized = normalize_retrieval(envelope())
    assert normalized.provider == "mitosis-cortex"
    assert normalized.sources[0].source_id == "src-1"
    assert normalized.sources[0].content_hash.startswith("sha256:")


def test_high_risk_without_sources_blocks(tmp_path: Path):
    result = evaluate_retrieval(envelope(riskLevel="high", sources=[]), tmp_path, as_of=AS_OF)
    assert result["decision"]["decision"] == "block"


def test_stale_source_requires_review(tmp_path: Path):
    result = evaluate_retrieval(
        envelope(sources=[source(validUntil="2026-07-01T00:00:00Z")]),
        tmp_path,
        as_of=AS_OF,
    )
    assert result["decision"]["decision"] == "review"
    assert result["decision"]["stale_source_ids"] == ["src-1"]


def test_high_risk_conflict_blocks(tmp_path: Path):
    sources = [
        source(universalId="src-1", contradicts=["src-2"]),
        source(universalId="src-2", excerpt="Contrary fact."),
    ]
    result = evaluate_retrieval(
        envelope(riskLevel="high", sources=sources),
        tmp_path,
        as_of=AS_OF,
    )
    assert result["decision"]["decision"] == "block"


def test_outputs_exclude_raw_query_and_excerpts(tmp_path: Path):
    evaluate_retrieval(envelope(), tmp_path, as_of=AS_OF)
    combined = "\n".join(
        (tmp_path / name).read_text(encoding="utf-8")
        for name in (
            "evidence-bundle.json",
            "policy-decision.json",
            "execution-receipt.json",
            "memory-event.json",
        )
    )
    assert "What should the agent do?" not in combined
    assert "A source-backed fact." not in combined


def test_finalize_creates_verified_receipt_event_and_economics(tmp_path: Path):
    evaluate_retrieval(envelope(), tmp_path, as_of=AS_OF)
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("verified output", encoding="utf-8")
    result = finalize_run(
        tmp_path,
        artifact,
        reviewer="Cody",
        provider="openai",
        model="gpt-test",
    )
    assert result["receipt"]["status"] == "verified"
    assert result["event"]["event_type"] == "execution_verified"
    assert result["economics"]["verification_passed"] is True


def test_blocked_run_cannot_finalize(tmp_path: Path):
    evaluate_retrieval(envelope(riskLevel="high", sources=[]), tmp_path, as_of=AS_OF)
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("output", encoding="utf-8")
    with pytest.raises(ValueError, match="blocked evidence"):
        finalize_run(tmp_path, artifact, reviewer="Cody")
