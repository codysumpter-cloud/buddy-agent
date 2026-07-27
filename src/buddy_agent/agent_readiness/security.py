"""Security evidence models and severity/confidence-aware gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Severity = Literal["info", "low", "medium", "high", "critical"]
Confidence = Literal["low", "medium", "high"]
Resolution = Literal["open", "fixed", "accepted-risk", "false-positive"]
GateDecision = Literal["pass", "review", "block"]

SEVERITY_ORDER: dict[Severity, int] = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
CONFIDENCE_ORDER: dict[Confidence, int] = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class SecurityFinding:
    check: str
    rule_id: str
    severity: Severity
    confidence: Confidence
    summary: str
    resolution: Resolution = "open"
    evidence_ref: str | None = None

    @property
    def unresolved(self) -> bool:
        return self.resolution == "open"


@dataclass(frozen=True)
class SecurityGatePolicy:
    required_checks: tuple[str, ...] = (
        "secret_scan",
        "dependency_scan",
        "static_analysis",
        "agent_security_review",
    )
    block_severity: Severity = "high"
    block_confidence: Confidence = "high"
    review_severity: Severity = "medium"
    review_confidence: Confidence = "high"


@dataclass(frozen=True)
class SecurityGateResult:
    decision: GateDecision
    missing_checks: tuple[str, ...]
    blocking_findings: tuple[SecurityFinding, ...]
    review_findings: tuple[SecurityFinding, ...]
    resolved_findings: int

    def to_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "missing_checks": list(self.missing_checks),
            "blocking_findings": [asdict(item) for item in self.blocking_findings],
            "review_findings": [asdict(item) for item in self.review_findings],
            "resolved_findings": self.resolved_findings,
        }


def _at_least(finding: SecurityFinding, severity: Severity, confidence: Confidence) -> bool:
    return SEVERITY_ORDER[finding.severity] >= SEVERITY_ORDER[severity] and CONFIDENCE_ORDER[finding.confidence] >= CONFIDENCE_ORDER[confidence]


def evaluate_security_gate(
    findings: list[SecurityFinding],
    checks_run: set[str],
    policy: SecurityGatePolicy | None = None,
) -> SecurityGateResult:
    selected = policy or SecurityGatePolicy()
    missing = tuple(sorted(set(selected.required_checks) - checks_run))
    unresolved = [finding for finding in findings if finding.unresolved]
    blocking = tuple(item for item in unresolved if _at_least(item, selected.block_severity, selected.block_confidence))
    review = tuple(
        item
        for item in unresolved
        if item not in blocking and _at_least(item, selected.review_severity, selected.review_confidence)
    )
    if blocking:
        decision: GateDecision = "block"
    elif missing or review:
        decision = "review"
    else:
        decision = "pass"
    return SecurityGateResult(
        decision=decision,
        missing_checks=missing,
        blocking_findings=blocking,
        review_findings=review,
        resolved_findings=sum(not item.unresolved for item in findings),
    )
