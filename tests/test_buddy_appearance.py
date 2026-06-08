from buddy_agent.buddy.appearance import BUDDY_ANIMATION_STATES, default_buddy_template
from buddy_agent.buddy.generate import default_ascii_frames, default_manifest


def test_default_buddy_template_matches_reference_style() -> None:
    template = default_buddy_template()

    assert "round_mint_body" in template.traits
    assert "heart_antler_ears" in template.traits
    assert "gold_heart_charm" in template.traits
    assert "navy_pixel_outline" in template.traits
    assert "belly_heart_charm" in template.customization_options


def test_default_manifest_declares_animation_cycle() -> None:
    manifest = default_manifest()

    assert manifest["states"] == list(BUDDY_ANIMATION_STATES)
    assert manifest["animation"] == {
        "states": list(BUDDY_ANIMATION_STATES),
        "frame_duration_ms": 900,
        "loop": True,
    }
    assert manifest["style_reference"]


def test_default_ascii_frames_are_visible_state_frames() -> None:
    frames = default_ascii_frames()

    assert tuple(frames) == BUDDY_ANIMATION_STATES
    assert len(set(frames.values())) == len(BUDDY_ANIMATION_STATES)
    assert all("default buddy" not in frame.lower() for frame in frames.values())
    assert "<3" in frames["idle"]
    assert "^ ^" in frames["happy"]
    assert "..." in frames["thinking"]
    assert "Zz" in frames["sleepy"]
