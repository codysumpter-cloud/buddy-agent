from pathlib import Path

from buddy_agent import BuddyAgentConfig


def test_config_loads_from_environment(monkeypatch):
    monkeypatch.setenv("BUDDY_HOME", "/tmp/buddy-agent-test")
    monkeypatch.setenv("BUDDY_ENABLE_GATEWAY", "true")
    monkeypatch.setenv("BUDDY_OMNI_ENABLED", "true")
    monkeypatch.setenv("BUDDY_OMNI_TIMEOUT_SECONDS", "30")

    config = BuddyAgentConfig.from_env()

    assert config.home == Path("/tmp/buddy-agent-test")
    assert config.enable_gateway is True
    assert config.omni.enabled is True
    assert config.omni.timeout_seconds == 30
