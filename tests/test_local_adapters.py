from buddy_agent import (
    LocalBuddyBrainAdapter,
    LocalKnowledgeVaultProvider,
    LocalOmniBuddyAdapter,
    LocalPrismtekAppBridge,
)


def test_local_buddy_brain_adapter_returns_context():
    adapter = LocalBuddyBrainAdapter(context={"AGENTS.md": "Use clean boundaries."})

    assert adapter.health().ok is True
    assert adapter.load_startup_context()["AGENTS.md"] == "Use clean boundaries."


def test_local_omni_adapter_routes_text_through_backend():
    adapter = LocalOmniBuddyAdapter()

    response = adapter.route_text("ping", metadata={"model": "test-model"}, context=("ctx",))

    assert response.startswith("Buddy runtime [test-model] processed: ping")
    assert "Context: ctx" in response


def test_local_app_bridge_records_events():
    bridge = LocalPrismtekAppBridge()

    bridge.publish_event("buddy.updated", {"buddy_id": "b1", "mood": "bright"})

    assert len(bridge.events) == 1
    assert bridge.events[0].buddy_id == "b1"
    assert bridge.events[0].body["mood"] == "bright"


def test_local_vault_provider_returns_sources():
    provider = LocalKnowledgeVaultProvider()
    provider.index.add("Buddy source text")

    results = provider.search("source")

    assert len(results) == 1
    assert results[0].title == "Local note"
    assert results[0].metadata["provider"] == "local"
