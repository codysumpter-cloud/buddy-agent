from buddy_agent.omni import OmniConfig


def test_default_omni_config_validates():
    config = OmniConfig()

    config.validate()

    assert config.route_mode == "hybrid"
    assert config.fallback_to_local is True
