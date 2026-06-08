from pathlib import Path

from buddy_agent.skills import load_skill_manifests, validate_skill_directory


def test_public_skills_validate() -> None:
    root = Path("skills/public")

    assert validate_skill_directory(root) == ()


def test_public_skills_are_safe_defaults() -> None:
    manifests = load_skill_manifests(Path("skills/public"))

    assert {manifest.name for manifest in manifests} == {
        "caps",
        "content-draft",
        "summarize",
        "vault-search-readonly",
    }
    assert {manifest.buddy.risk_class for manifest in manifests} <= {"read-only", "draft-only"}
    assert all(not manifest.buddy.auto_executable for manifest in manifests)
