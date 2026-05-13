from buddy_agent.companion import CompanionPermissionPolicy, PermissionRequest


def test_companion_policy_allows_user_opened_chat():
    policy = CompanionPermissionPolicy()

    result = policy.decide(PermissionRequest(capability="chat", reason="open", user_initiated=True))

    assert result.decision == "allow"


def test_companion_policy_asks_for_extra_context_bridge():
    policy = CompanionPermissionPolicy()

    result = policy.decide(
        PermissionRequest(capability="context_bridge", reason="helper context", user_initiated=True)
    )

    assert result.decision == "ask"
