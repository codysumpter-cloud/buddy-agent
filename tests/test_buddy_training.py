from pathlib import Path

from buddy_agent.training import BuddyTrainingEngine, BuddyTrainingStore
from buddy_agent.training.models import BuddyTrainingState, parse_training_action


def test_training_reward_updates_state():
    state = BuddyTrainingState()
    result = BuddyTrainingEngine().apply(state, "quest_completed")

    assert result.reward.xp == 24
    assert result.state.lifetime_xp == 24
    assert result.state.sparks == 3
    assert result.state.snacks == 1
    assert result.state.stats.discipline == 3
    assert result.state.stats.reliability == 3
    assert result.state.last_action == "quest_completed"


def test_training_unlocks_first_achievement():
    state = BuddyTrainingState()
    engine = BuddyTrainingEngine()

    engine.apply(state, "quest_completed")
    result = engine.apply(state, "chat")

    assert "first-sparks" in result.state.achievements
    assert "first-sparks" in result.new_achievements


def test_training_store_round_trips(tmp_path: Path):
    path = tmp_path / "training-state.json"
    store = BuddyTrainingStore(path)
    state = BuddyTrainingState(buddy_id="test-buddy", level=2, xp=10)
    state.achievements.add("first-sparks")

    store.save(state)
    loaded = store.load()

    assert loaded.buddy_id == "test-buddy"
    assert loaded.level == 2
    assert loaded.xp == 10
    assert loaded.achievements == {"first-sparks"}


def test_parse_training_action_rejects_unknown_action():
    try:
        parse_training_action("unsupported_action")
    except ValueError as error:
        assert "Unsupported Buddy Training action" in str(error)
    else:
        raise AssertionError("Expected unknown training action to fail")
