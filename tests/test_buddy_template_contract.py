from buddy_agent.buddy.appearance import default_buddy_template
from buddy_agent.buddy.generate import default_manifest
from buddy_agent.buddy.render_contract import validate_buddy_manifest


def test_default_buddy_template_validates():
    template = default_buddy_template()

    assert template.key == "default-buddy"
    assert template.canvas_size == 64
    assert template.states == ("idle", "happy", "thinking", "sleepy")


def test_default_manifest_validates_for_app_renderer():
    manifest = default_manifest()

    validate_buddy_manifest(manifest)

    assert manifest["template"] == "default-buddy"
