from buddy_agent.memory import NoteIndex


def test_note_index_adds_and_finds_notes():
    index = NoteIndex()
    note = index.add("Buddy likes clean adapter seams.", tags=("architecture",))

    results = index.find("adapter")

    assert results == (note,)
    assert note.tags == ("architecture",)


def test_note_index_empty_query_returns_recent_notes():
    index = NoteIndex()
    first = index.add("one")
    second = index.add("two")

    assert index.find("") == (first, second)
