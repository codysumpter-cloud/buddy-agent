from buddy_agent.sandbox import ConservativeSkillPolicy, SkillExecutionRequest


def decide(risk_class: str) -> str:
    request = SkillExecutionRequest(skill_name="demo", risk_class=risk_class)
    return ConservativeSkillPolicy().decide(request).decision


def test_read_only_allowed() -> None:
    assert decide("read-only") == "allow"


def test_draft_only_allowed() -> None:
    assert decide("draft-only") == "allow"


def test_external_action_review() -> None:
    assert decide("external-action") == "review"


def test_money_denied() -> None:
    assert decide("money") == "deny"


def test_credential_denied() -> None:
    assert decide("credential") == "deny"


def test_destructive_denied() -> None:
    assert decide("destructive") == "deny"
