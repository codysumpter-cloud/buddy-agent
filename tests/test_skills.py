from buddy_agent.skills import SkillDefinition, SkillRegistry


def test_skill_registry_runs_registered_skill():
    registry = SkillRegistry()
    registry.register(
        SkillDefinition(
            name="shout",
            description="Uppercase input.",
            handler=lambda text: text.upper(),
            metadata={},
        )
    )

    assert registry.names() == ("shout",)
    assert registry.run("shout", "buddy") == "BUDDY"
