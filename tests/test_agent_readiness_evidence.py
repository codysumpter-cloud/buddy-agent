from buddy_agent.agent_readiness.economics import TaskEconomics
from buddy_agent.agent_readiness.evidence import TaskEvidenceBundle
from buddy_agent.agent_readiness.security import evaluate_security_gate


def test_evidence_bundle_maps_to_existing_receipt_status():
    economics = TaskEconomics("task", "openai", "gpt-test", 1, 0, 0, 10, 0, True, True, security_gate="pass")
    security = evaluate_security_gate([], {"secret_scan", "dependency_scan", "static_analysis", "agent_security_review"})
    receipt = TaskEvidenceBundle("agent.task", "verified task", economics, security, ("tests",), ("artifact",)).to_receipt()
    assert receipt.status == "ok"
    assert receipt.metadata["economics"]["verified_completion"] is True
