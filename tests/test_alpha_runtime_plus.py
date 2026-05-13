from buddy_agent.alpha import BuddyAlphaRuntime
from buddy_agent.app_bridge import AppChatRequest, route_app_chat
from buddy_agent.local_adapters import LocalKnowledgeVaultProvider, LocalPrismtekAppBridge
from buddy_agent.memory import PersistentNoteIndex
from buddy_agent.runtime import RuntimeEngine


def test_alpha_runtime_chat_uses_retrieval_and_app_bridge(tmp_path):
    memory = PersistentNoteIndex(tmp_path / "memory.json")
    memory.add("Buddy retrieval source is available", tags=("test",))
    app_bridge = LocalPrismtekAppBridge()
    runtime = BuddyAlphaRuntime(
        engine=RuntimeEngine(session_id="alpha-test"),
        memory=memory,
        vault=LocalKnowledgeVaultProvider(index=memory),
        app_bridge=app_bridge,
    )

    result = runtime.chat("retrieval")

    assert result.ok is True
    assert "Buddy runtime [buddy-local] processed: retrieval" in result.message
    assert "Local note: Buddy retrieval source is available" in result.message
    assert app_bridge.events[-1].name == "buddy.updated"


def test_alpha_runtime_app_chat_route(tmp_path):
    memory = PersistentNoteIndex(tmp_path / "memory.json")
    runtime = BuddyAlphaRuntime(memory=memory, vault=LocalKnowledgeVaultProvider(index=memory))

    response = route_app_chat(
        runtime,
        AppChatRequest(prompt="hello from app", surface="widget", buddy_id="ignored"),
    )

    assert response.ok is True
    assert response.surface == "widget"
    assert response.buddy_id == "default-buddy"
    assert "hello from app" in response.message


def test_alpha_runtime_smoke_exercises_plus_path(tmp_path):
    memory = PersistentNoteIndex(tmp_path / "memory.json")
    runtime = BuddyAlphaRuntime(memory=memory, vault=LocalKnowledgeVaultProvider(index=memory))

    results = runtime.smoke()

    assert all(result.ok for result in results)
    assert any("default Buddy template valid" in result.message for result in results)
    assert any("HELLO" not in result.message for result in results)
    assert runtime.app_bridge.events
