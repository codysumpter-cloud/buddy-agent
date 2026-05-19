from pathlib import Path

import pytest

from buddy_agent.skills import SkillManifestError, load_skill_manifest, validate_skill_directory


def write_skill(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "SKILL.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_skill_manifest_parses_frontmatter(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        """---
name: demo
description: Safe demo skill.
version: 0.1.0
platforms:
  - local
metadata:
  owner: Prismtek
buddy:
  risk_class: read-only
  auto_executable: false
  requires_explicit_approval: true
---
# Body
""",
    )

    manifest = load_skill_manifest(path)

    assert manifest.name == "demo"
    assert manifest.description == "Safe demo skill."
    assert manifest.platforms == ("local",)
    assert manifest.metadata["owner"] == "Prismtek"
    assert manifest.buddy.risk_class == "read-only"
    assert manifest.buddy.requires_explicit_approval is True


def test_skill_manifest_requires_frontmatter_at_byte_zero(tmp_path: Path) -> None:
    path = write_skill(tmp_path, "\n---\nname: demo\ndescription: nope\n---\n")

    with pytest.raises(SkillManifestError):
        load_skill_manifest(path)


def test_skill_manifest_rejects_invalid_name(tmp_path: Path) -> None:
    path = write_skill(tmp_path, "---\nname: bad name\ndescription: nope\n---\n")

    with pytest.raises(SkillManifestError):
        load_skill_manifest(path)


def test_skill_manifest_rejects_long_description(tmp_path: Path) -> None:
    description = "x" * 1024
    manifest_text = f"---\nname: demo\ndescription: {description}\n---\n"
    path = write_skill(tmp_path, manifest_text)

    with pytest.raises(SkillManifestError):
        load_skill_manifest(path)


def test_validate_skill_directory_reports_duplicates(tmp_path: Path) -> None:
    first = tmp_path / "a"
    second = tmp_path / "b"
    first.mkdir()
    second.mkdir()
    first_manifest = "---\nname: demo\ndescription: one\n---\n"
    second_manifest = "---\nname: demo\ndescription: two\n---\n"
    (first / "SKILL.md").write_text(first_manifest, encoding="utf-8")
    (second / "SKILL.md").write_text(second_manifest, encoding="utf-8")

    problems = validate_skill_directory(tmp_path)

    assert any("duplicate skill name" in problem for problem in problems)
