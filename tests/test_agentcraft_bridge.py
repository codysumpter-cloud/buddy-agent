from buddy_agent.integrations.agentcraft import (
    AgentCraftBridge,
    AgentCraftConfig,
    AgentCraftEvent,
    is_local_http_endpoint,
    parse_payload_json,
    redact_value,
)


def test_agentcraft_bridge_is_disabled_by_default():
    bridge = AgentCraftBridge(AgentCraftConfig(enabled=False))

    result = bridge.emit(AgentCraftEvent("mission_start", {"prompt": "ship the thing"}))

    assert result.ok is True
    assert result.skipped is True
    assert result.reason == "BUDDY_AGENTCRAFT_ENABLED is not set"
    assert result.event["prompt"] == "[redacted]"


def test_agentcraft_redacts_secret_like_values():
    fake_openai = "sk-" + "1" * 20
    fake_github = "ghp_" + "a" * 20
    redacted = redact_value(
        {
            "api_key": fake_openai,
            "nested": {"authorization": "Bearer " + "b" * 20},
            "command": "echo " + fake_github,
        }
    )

    assert redacted == {
        "api_key": "[redacted]",
        "nested": {"authorization": "[redacted]"},
        "command": "echo gh_[redacted]",
    }


def test_agentcraft_endpoint_must_be_local_http():
    assert is_local_http_endpoint("http://localhost:2468/event") is True
    assert is_local_http_endpoint("https://127.0.0.1:2468/event") is True
    assert is_local_http_endpoint("https://example.com/event") is False
    assert is_local_http_endpoint("file:///tmp/event") is False


def test_agentcraft_rejects_non_object_payload():
    try:
        parse_payload_json("[]")
    except ValueError as error:
        assert "payload must be a JSON object" in str(error)
    else:
        raise AssertionError("Expected non-object payload to fail")
