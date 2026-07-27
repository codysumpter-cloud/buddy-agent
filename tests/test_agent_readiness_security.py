from buddy_agent.agent_readiness.security import (
    SecurityFinding,
    evaluate_security_gate,
)

REQUIRED = {"secret_scan", "dependency_scan", "static_analysis", "agent_security_review"}


def test_high_confidence_high_severity_blocks():
    result = evaluate_security_gate([
        SecurityFinding("agent_security_review", "path-traversal", "high", "high", "unsafe path")
    ], REQUIRED)
    assert result.decision == "block"
    assert len(result.blocking_findings) == 1


def test_medium_high_requires_review_and_resolved_finding_does_not():
    open_result = evaluate_security_gate([
        SecurityFinding("static_analysis", "unsafe-data", "medium", "high", "unsafe data")
    ], REQUIRED)
    fixed_result = evaluate_security_gate([
        SecurityFinding("static_analysis", "unsafe-data", "high", "high", "unsafe data", resolution="fixed")
    ], REQUIRED)
    assert open_result.decision == "review"
    assert fixed_result.decision == "pass"


def test_missing_required_check_requires_review():
    result = evaluate_security_gate([], {"secret_scan"})
    assert result.decision == "review"
    assert "dependency_scan" in result.missing_checks
