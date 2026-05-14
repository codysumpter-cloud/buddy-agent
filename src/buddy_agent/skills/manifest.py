"""Safe SKILL.md manifest parsing.

The loader reads YAML-like frontmatter only. It never imports, evaluates, or executes
content from skill directories.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
RISK_CLASSES = {
    "read-only",
    "draft-only",
    "write",
    "external-action",
    "destructive",
    "money",
    "identity",
    "location",
    "credential",
    "repo-mutation",
}


class SkillManifestError(ValueError):
    """Raised when a skill manifest is missing or invalid."""


@dataclass(frozen=True)
class BuddySkillMetadata:
    """Buddy-specific skill policy metadata."""

    risk_class: str = "read-only"
    auto_executable: bool = False
    requires_explicit_approval: bool = False


@dataclass(frozen=True)
class SkillManifest:
    """Validated SKILL.md frontmatter."""

    name: str
    description: str
    path: Path
    version: str | None = None
    author: str | None = None
    license: str | None = None
    platforms: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    buddy: BuddySkillMetadata = field(default_factory=BuddySkillMetadata)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    return _strip_quotes(value)


def _parse_frontmatter(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0:
            key, separator, value = line.partition(":")
            if separator != ":":
                raise SkillManifestError(f"Invalid frontmatter line: {raw_line}")
            current_key = key.strip()
            if not current_key:
                raise SkillManifestError("Frontmatter contains an empty key")
            data[current_key] = _parse_scalar(value) if value.strip() else {}
            continue
        if current_key is None:
            raise SkillManifestError(f"Nested value without parent key: {raw_line}")
        if line.startswith("- "):
            existing = data.get(current_key)
            if not isinstance(existing, list):
                existing = []
                data[current_key] = existing
            existing.append(_parse_scalar(line[2:]))
            continue
        key, separator, value = line.partition(":")
        if separator != ":":
            raise SkillManifestError(f"Invalid nested frontmatter line: {raw_line}")
        existing_map = data.get(current_key)
        if not isinstance(existing_map, dict):
            existing_map = {}
            data[current_key] = existing_map
        existing_map[key.strip()] = _parse_scalar(value)
    return data


def _manifest_path(path: Path) -> Path:
    return path / "SKILL.md" if path.is_dir() else path


def _required_string(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SkillManifestError(f"Missing required field: {key}")
    return value.strip()


def _optional_string(data: Mapping[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise SkillManifestError(f"Field must be a string: {key}")
    return value.strip() or None


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    raise SkillManifestError("platforms must be a string or list")


def _string_map(value: object, *, field_name: str) -> Mapping[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SkillManifestError(f"{field_name} must be a mapping")
    return {str(key): str(item_value) for key, item_value in value.items()}


def _bool_value(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    raise SkillManifestError("Buddy boolean metadata must be true or false")


def _buddy_metadata(value: object) -> BuddySkillMetadata:
    if value is None:
        return BuddySkillMetadata()
    if not isinstance(value, dict):
        raise SkillManifestError("buddy metadata must be a mapping")
    buddy = cast(dict[str, Any], value)
    risk_class = str(buddy.get("risk_class", "read-only")).strip().lower()
    if risk_class not in RISK_CLASSES:
        raise SkillManifestError(f"Unknown risk_class: {risk_class}")
    return BuddySkillMetadata(
        risk_class=risk_class,
        auto_executable=_bool_value(buddy.get("auto_executable"), default=False),
        requires_explicit_approval=_bool_value(
            buddy.get("requires_explicit_approval"), default=False
        ),
    )


def load_skill_manifest(path: Path) -> SkillManifest:
    """Load and validate SKILL.md frontmatter without executing code."""
    manifest_path = _manifest_path(path)
    text = manifest_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SkillManifestError("SKILL.md must start with YAML frontmatter at byte 0")
    lines = text.splitlines()
    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line == "---"), None
    )
    if closing_index is None:
        raise SkillManifestError("SKILL.md frontmatter is missing a closing delimiter")
    data = _parse_frontmatter(lines[1:closing_index])
    name = _required_string(data, "name")
    if not NAME_PATTERN.fullmatch(name):
        raise SkillManifestError(f"Invalid skill name: {name}")
    description = _required_string(data, "description")
    if len(description) >= 1024:
        raise SkillManifestError("Skill description must be under 1024 characters")
    return SkillManifest(
        name=name,
        description=description,
        path=manifest_path,
        version=_optional_string(data, "version"),
        author=_optional_string(data, "author"),
        license=_optional_string(data, "license"),
        platforms=_string_tuple(data.get("platforms")),
        metadata=_string_map(data.get("metadata"), field_name="metadata"),
        buddy=_buddy_metadata(data.get("buddy")),
    )


def load_skill_manifests(root: Path) -> tuple[SkillManifest, ...]:
    """Load all SKILL.md manifests under a root directory."""
    if not root.exists():
        return ()
    return tuple(load_skill_manifest(path) for path in sorted(root.rglob("SKILL.md")))


def validate_skill_directory(root: Path) -> tuple[str, ...]:
    """Validate all manifests under a root and return problem strings."""
    if not root.exists():
        return (f"Skill path does not exist: {root}",)
    skill_paths = tuple(sorted(root.rglob("SKILL.md")))
    if not skill_paths:
        return (f"No SKILL.md manifests found under: {root}",)
    problems: list[str] = []
    names: set[str] = set()
    for path in skill_paths:
        try:
            manifest = load_skill_manifest(path)
        except SkillManifestError as exc:
            problems.append(f"{path}: {exc}")
            continue
        if manifest.name in names:
            problems.append(f"{path}: duplicate skill name: {manifest.name}")
        names.add(manifest.name)
    return tuple(problems)


def find_skill_manifest(root: Path, name: str) -> SkillManifest | None:
    """Find one manifest by skill name."""
    for manifest in load_skill_manifests(root):
        if manifest.name == name:
            return manifest
    return None
