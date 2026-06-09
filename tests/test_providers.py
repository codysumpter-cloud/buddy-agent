from buddy_agent.providers import (
    LocalEchoProvider,
    ProviderRequest,
    create_provider_from_env,
    provider_names,
)


def test_local_echo_provider_responds_offline():
    provider = LocalEchoProvider()

    response = provider.respond(ProviderRequest(content="hello", session_id="s1"))

    assert response.content == "Buddy local echo: hello"
    assert response.provider == "local"
    assert response.metadata["network"] == "disabled"


def test_provider_selection_defaults_to_local():
    provider = create_provider_from_env({})

    assert provider.name == "local"


def test_unknown_provider_falls_back_to_local_when_network_disabled():
    provider = create_provider_from_env(
        {"BUDDY_PROVIDER": "remote", "BUDDY_NETWORK_ENABLED": "false"}
    )

    assert provider.name == "local"


def test_provider_names_contains_local():
    assert provider_names() == ("local",)
