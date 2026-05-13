from buddy_agent.alpha import BuddyAlphaRuntime
from buddy_agent.memory import PersistentNoteIndex


def test_alpha_runtime_chat_skill_and_template(tmp_path):
    runtime = BuddyAlphaRuntime(memory=PersistentNoteIndex(tmp_path / "memory.json"))

    assert runtime.validate_template().ok is True
    assert runtime.chat("hello").ok is True
    assert runtime.run_skill("caps", "buddy").message == "BUDDY"


def test_alpha_runtime_memory_persists_with_shared_path(tmp_path):
    path = tmp_path / "memory.json"
    first = BuddyAlphaRuntime(memory=PersistentNoteIndex(path))
    first.remember("Buddy alpha memory online.")

    second = BuddyAlphaRuntime(memory=PersistentNoteIndex(path))
    result = second.recall("online")

    assert "Buddy alpha memory online." in result.message
