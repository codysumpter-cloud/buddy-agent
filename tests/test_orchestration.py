import json

from buddy_agent.orchestration import BuddyOrchestrator
from buddy_agent.orchestration.demo import main as demo_main


def test_buddy_orchestrator_delegates_and_reviews():
    trace = BuddyOrchestrator().run("Draft a safe project note")

    assert trace["task"]["orchestrator"] == "Buddy"
    assert trace["task"]["worker"] == "Lil Buddy"
    assert trace["task"]["review_required"] is True
    assert trace["result"]["needs_buddy_review"] is True
    assert trace["review"]["status"] == "approved"
    assert "Buddy reviewed" in trace["final_response"]


def test_buddy_orchestrator_escalates_high_risk_intent():
    trace = BuddyOrchestrator().run("Use the camera and send an account update")

    assert trace["task"]["safety_class"] == "high"
    assert trace["review"]["status"] == "escalate"
    assert trace["review"]["escalation_required"] is True


def test_demo_cli_prints_json(capsys):
    assert demo_main(["Draft", "a", "safe", "project", "note"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["task"]["schema_version"] == "buddy.task.v1"
    assert payload["result"]["schema_version"] == "buddy.result.v1"
    assert "system_prompt_template" in payload
