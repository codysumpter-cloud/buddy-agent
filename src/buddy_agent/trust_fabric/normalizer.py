"""Normalize retrieval-provider output into Prismtek evidence contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .models import EvidenceSource, RetrievalEnvelope

RISK_LEVELS = {"low", "medium", "high", "critical"}
TRUST_TIERS = {"authoritative", "verified", "supporting", "untrusted"}


def _first(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_retrieval(payload: dict[str, Any]) -> RetrievalEnvelope:
    query = str(_first(payload, "query", "question", default=""))
    retrieved_at = str(_first(payload, "retrieved_at", "retrievedAt", "timestamp", default=_iso_now()))
    provider = str(_first(payload, "provider", "vendor", default="unknown"))
    agent_id = str(_first(payload, "agent_id", "agentId", "agent", default="buddy"))
    risk_level = str(_first(payload, "risk_level", "riskLevel", default="medium")).lower()
    if risk_level not in RISK_LEVELS:
        raise ValueError(f"unsupported risk level: {risk_level}")
    task_id = str(_first(payload, "task_id", "taskId", default=""))
    if not task_id:
        task_id = f"trust-{hashlib.sha256((provider + query + retrieved_at).encode()).hexdigest()[:16]}"

    raw_sources = _first(payload, "sources", "results", "evidence", default=[])
    if not isinstance(raw_sources, list):
        raise ValueError("sources/results/evidence must be a list")

    sources: list[EvidenceSource] = []
    for index, raw in enumerate(raw_sources):
        if not isinstance(raw, dict):
            raise ValueError(f"source {index} must be an object")
        source_id = str(_first(raw, "source_id", "sourceId", "universalId", "id", default=f"source-{index + 1}"))
        excerpt = str(_first(raw, "excerpt", "content", "text", "snippet", default=""))
        content_hash = str(_first(raw, "content_hash", "contentHash", "sha256", default="")) or _digest(excerpt)
        confidence = float(_first(raw, "confidence", "score", default=0.5))
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"source {source_id} confidence must be between 0 and 1")
        trust_tier = str(_first(raw, "trust_tier", "trustTier", default="supporting")).lower()
        if trust_tier not in TRUST_TIERS:
            raise ValueError(f"source {source_id} has unsupported trust tier: {trust_tier}")
        supports = tuple(str(item) for item in _first(raw, "supports", default=[]) or [])
        contradicts = tuple(str(item) for item in _first(raw, "contradicts", "conflicts_with", default=[]) or [])
        metadata = _first(raw, "metadata", default={})
        if not isinstance(metadata, dict):
            raise ValueError(f"source {source_id} metadata must be an object")
        sources.append(
            EvidenceSource(
                source_id=source_id,
                source_type=str(_first(raw, "source_type", "sourceType", "type", default="unknown")),
                excerpt=excerpt,
                observed_at=_first(raw, "observed_at", "observedAt", "source_timestamp", "sourceTimestamp"),
                valid_until=_first(raw, "valid_until", "validUntil", "expires_at", "expiresAt"),
                confidence=confidence,
                trust_tier=trust_tier,
                content_hash=content_hash,
                supports=supports,
                contradicts=contradicts,
                metadata=metadata,
            )
        )

    return RetrievalEnvelope(
        provider=provider,
        task_id=task_id,
        agent_id=agent_id,
        risk_level=risk_level,
        retrieved_at=retrieved_at,
        query_digest=_digest(query),
        sources=tuple(sources),
    )


def load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload
