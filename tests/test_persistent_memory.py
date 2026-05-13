from buddy_agent.memory import PersistentNoteIndex


def test_persistent_memory_round_trips_between_instances(tmp_path):
    path = tmp_path / "memory.json"
    first = PersistentNoteIndex(path)

    first.add("Prismtek likes clean runtime seams", tags=("alpha",))
    second = PersistentNoteIndex(path)

    matches = second.find("runtime")
    assert len(matches) == 1
    assert matches[0].text == "Prismtek likes clean runtime seams"
    assert matches[0].tags == ("alpha",)
