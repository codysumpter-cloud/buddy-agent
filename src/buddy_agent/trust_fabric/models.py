"""Data contracts for the Prismtek Trust Fabric."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceSource:
    source_id: str
    source_type: str
    excerpt: str
    observed_at: str | None
    valid_until: str | None
    confidence: float
    trust_tier: str
    content_hash: str
    supports: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def public_dict(self, *, include_excerpt: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload["supports"] = list(self.supports)
        payload["contradicts"] = list(self.contradicts)
        if not include_excerpt:
            payload.pop("excerpt", None)
        return payload


@dataclass(frozen=True)
class RetrievalEnvelope:
    provider: str
    task_id: str
    agent_id: str
    risk_level: str
    retrieved_at: str
    query_digest: str
    sources: tuple[EvidenceSource, ...]


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    reasons: tuple[str, ...]
    required_actions: tuple[str, ...]
    stale_source_ids: tuple[str, ...]
    conflicting_source_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reasons": list(self.reasons),
            "required_actions": list(self.required_actions),
            "stale_source_ids": list(self.stale_source_ids),
            "conflicting_source_ids": list(self.conflicting_source_ids),
        }
