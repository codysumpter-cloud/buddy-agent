"""Admissibility policy for retrieved evidence."""

from __future__ import annotations

from datetime import UTC, datetime

from .models import PolicyDecision, RetrievalEnvelope


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def evaluate_policy(envelope: RetrievalEnvelope, *, as_of: str | None = None) -> PolicyDecision:
    now = _parse_iso(as_of) if as_of else datetime.now(UTC)
    assert now is not None
    reasons: list[str] = []
    actions: list[str] = []
    stale: list[str] = []
    conflicts: set[str] = set()
    severity = 0  # allow=0, review=1, block=2

    if not envelope.sources:
        reasons.append("No source evidence was supplied.")
        actions.append("Retrieve cited source evidence before relying on the result.")
        severity = 2 if envelope.risk_level in {"high", "critical"} else 1

    source_ids = {source.source_id for source in envelope.sources}
    for source in envelope.sources:
        valid_until = _parse_iso(source.valid_until)
        if valid_until and valid_until < now:
            stale.append(source.source_id)
            reasons.append(f"Source {source.source_id} is stale.")
            actions.append(f"Refresh or explicitly approve stale source {source.source_id}.")
            severity = max(
                severity,
                2
                if envelope.risk_level in {"high", "critical"}
                and source.trust_tier == "authoritative"
                else 1,
            )
        if source.observed_at is None and envelope.risk_level in {"medium", "high", "critical"}:
            reasons.append(f"Source {source.source_id} has no observed timestamp.")
            actions.append(f"Add an observed timestamp for source {source.source_id}.")
            severity = max(severity, 1)
        if source.confidence < 0.35 and envelope.risk_level in {"high", "critical"}:
            reasons.append(f"Source {source.source_id} has critically low confidence.")
            actions.append(f"Replace or corroborate source {source.source_id}.")
            severity = 2
        elif source.confidence < 0.6:
            reasons.append(f"Source {source.source_id} has low confidence.")
            actions.append(f"Corroborate source {source.source_id}.")
            severity = max(severity, 1)
        for other in source.contradicts:
            conflicts.add(source.source_id)
            if other in source_ids:
                conflicts.add(other)

    if conflicts:
        reasons.append("The evidence set contains explicit source conflicts.")
        actions.append("Resolve conflicting sources or obtain a human adjudication.")
        severity = max(severity, 2 if envelope.risk_level in {"high", "critical"} else 1)

    if envelope.risk_level in {"high", "critical"} and envelope.sources:
        strong = [
            source
            for source in envelope.sources
            if source.trust_tier in {"authoritative", "verified"}
            and source.confidence >= 0.7
            and source.source_id not in stale
        ]
        if not strong:
            reasons.append("High-risk work lacks a current authoritative or verified source.")
            actions.append(
                "Add a current authoritative or verified source with confidence of at least 0.7."
            )
            severity = 2

    decision = ("allow", "review", "block")[severity]
    if decision == "allow":
        reasons.append("Evidence satisfies the configured admissibility policy.")
    return PolicyDecision(
        decision=decision,
        reasons=tuple(dict.fromkeys(reasons)),
        required_actions=tuple(dict.fromkeys(actions)),
        stale_source_ids=tuple(sorted(set(stale))),
        conflicting_source_ids=tuple(sorted(conflicts)),
    )
