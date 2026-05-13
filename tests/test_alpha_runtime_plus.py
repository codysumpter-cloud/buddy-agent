import json
from collections.abc import Mapping
from pathlib import Path

from buddy_agent import BuddyAgentConfig, BuddyRuntimeEntrypoint
from buddy_agent.alpha import BuddyAlphaRuntime
from buddy_agent.app_bridge import BuddyAppChatResponse
from buddy_agent.companion import CompanionShell
from buddy_agent.local_adapters import LocalOmniBuddyAdapter, LocalPrismtekAppBridge
from buddy_agent.memory import PersistentNoteIndex


def test_config_file_runtime_entrypoint_uses_memory_path(tmp_path):
    config_path = tmp_path / "buddy.json"
    memory_path = tmp_path / "memory.json"
    config_path.write_text(
        json.dumps(
            {
                "home": str(tmp_path),
                "memory_path": str(memory_path),
                "operator_profile": "test-operator",
                "omni": {"enabled": True, "model": "test-local"},
            }
        ),
        encoding="utf-8",
    )

    entrypoint = BuddyRuntimeEntrypoint.from_config_file(config_path)
    result = entrypoint.execute("chat", "hello")

    assert result.ok is True
    assert "test-local" in result.message
    assert entrypoint.runtime.config.resolved_memory_path == memory_path


def test_local_model_routing_calls_injected_backend(tmp_path):
    calls = []

    def backend(prompt: str, metadata: Mapping[str, str]) -> str:
        calls.append((prompt, metadata))
        return f"backend:{prompt}:{metadata['operator']}"

    runtime = BuddyAlphaRuntime(
        memory=PersistentNoteIndex(tmp_path / "memory.json"),
        omni=LocalOmniBuddyAdapter(backend=backend, backend_name="test-backend"),
    )

    result = runtime.chat("ping")

    assert result.message.startswith("backend:ping:")
    assert calls[0][0] == "ping"
    assert calls[0][1]["source_count"] == "0"


def test_retrieval_uses_persistent_memory_provider(tmp_path):
    runtime = BuddyAlphaRuntime(memory=PersistentNoteIndex(tmp_path / "memory.json"))
    runtime.remember("runtime seams should stay clean")

    sources = runtime.retrieve("runtime")
    chat = runtime.chat("runtime")

    assert sources[0].text == "runtime seams should stay clean"
    assert "sources=Local note" in chat.detail


def test_app_chat_bridge_publishes_event(tmp_path):
    bridge = LocalPrismtekAppBridge()
    runtime = BuddyAlphaRuntime(
        memory=PersistentNoteIndex(tmp_path / "memory.json"),
        app_bridge=bridge,
    )

    response = runtime.app_chat("buddy-1", "hello buddy")

    assert isinstance(response, BuddyAppChatResponse)
    assert response.ok is True
    assert bridge.events[0].buddy_id == "buddy-1"
    assert bridge.events[0].body["surface"] == "chat"


def test_companion_shell_loads_default_template():
    shell = CompanionShell.load(Path("templates/default-buddy/buddy.json"))

    assert shell.display_name == "Default Buddy"
    assert shell.manifest["canvas"] == {"width": 64, "height": 64}


def test_restricted_integrations_default_disabled(tmp_path):
    config = BuddyAgentConfig.from_mapping({"home": str(tmp_path)})

    assert config.restricted_integrations_enabled is False
