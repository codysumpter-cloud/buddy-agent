from buddy_agent.agent_readiness.checkpoint import (
    InMemoryCheckpointAdapter,
    UsageTotals,
    run_checkpoint_smoke,
)


def test_checkpoint_restore_preserves_usage_trace_and_listener_lifecycle():
    result = run_checkpoint_smoke(InMemoryCheckpointAdapter())
    assert result.ok
    assert result.final_usage == UsageTotals(
        input_tokens=140,
        output_tokens=35,
        tool_calls=1,
        model_cost=0.015,
        tool_cost=0.002,
    )
    assert not result.hosted_multi_agent_enabled
