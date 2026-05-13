from buddy_agent.memory import PersistentNoteIndex


def test_persistent_note_index_round_trips(tmp_path):
    path = tmp_path / "memory.json"
    first = PersistentNoteIndex(path)
    first.add("Buddy remembers alpha runtime.")

    second = PersistentNoteIndex(path)
    results = second.find("alpha")

    assert len(results) == 1
    assert results[0].text == "Buddy remembers alpha runtime."
