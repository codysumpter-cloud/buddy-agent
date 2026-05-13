from buddy_agent.sandbox import ConservativeExecutionPolicy, ExecutionRequest


def test_conservative_execution_policy_reviews_by_default():
    policy = ConservativeExecutionPolicy()

    decision = policy.decide(ExecutionRequest(command="echo hello"))

    assert decision.decision == "review"
    assert "Manual review" in decision.reason
