from buddy_agent.buddy import BuddyArchetype, BuddyProfile


def test_buddy_profile_clamps_care_stats():
    archetype = BuddyArchetype(
        key="helper",
        name="Helper",
        description="A practical support buddy.",
    )
    profile = BuddyProfile(
        buddy_id="buddy-1",
        display_name="Buddy",
        archetype=archetype,
        energy=150,
        attention=-10,
    )

    profile.clamp_stats()

    assert profile.energy == 100
    assert profile.attention == 0
