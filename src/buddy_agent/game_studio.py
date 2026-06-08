"""VS Code + engine project helpers for Buddy Game Studio.

The helpers intentionally do not launch Godot, Unity, shell commands, or AI agents. They
create reviewable workspace files and a lightweight project index that a human or guarded
agent can inspect.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

EngineName = Literal["godot", "unity"]

SUPPORTED_ENGINES: tuple[EngineName, ...] = ("godot", "unity")

IGNORED_DIRECTORIES = {
    ".buddy",
    ".git",
    ".godot",
    ".vscode",
    "__pycache__",
    "Library",
    "Temp",
    "Obj",
    "Build",
    "Builds",
    "Logs",
    "UserSettings",
    "node_modules",
    "imported",
}

SCENE_SUFFIXES = {".tscn", ".scn", ".unity"}
SCRIPT_SUFFIXES = {".gd", ".cs", ".shader", ".compute", ".gdshader"}
ASSET_SUFFIXES = {
    ".ase",
    ".aseprite",
    ".bmp",
    ".gif",
    ".jpg",
    ".jpeg",
    ".json",
    ".mp3",
    ".ogg",
    ".png",
    ".svg",
    ".tres",
    ".wav",
    ".webp",
}


@dataclass(frozen=True)
class EngineDetection:
    """Result of inspecting a game project directory."""

    root: Path
    engine: EngineName | None
    confidence: Literal["high", "medium", "low", "ambiguous", "none"]
    reasons: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Return true when one supported engine was detected."""

        return self.engine is not None and self.confidence != "ambiguous"


@dataclass(frozen=True)
class GameStudioInitResult:
    """Files written by the VS Code scaffold initializer."""

    root: Path
    engine: EngineName
    files_written: tuple[Path, ...]
    files_skipped: tuple[Path, ...]

    def summary_lines(self) -> tuple[str, ...]:
        """Return CLI-friendly summary lines."""

        lines = [
            f"ok game-studio: initialized {self.engine} workspace at {self.root}",
            f"files_written={len(self.files_written)}",
            f"files_skipped={len(self.files_skipped)}",
        ]
        lines.extend(f"wrote {path}" for path in self.files_written)
        lines.extend(f"skipped existing {path}" for path in self.files_skipped)
        return tuple(lines)


@dataclass(frozen=True)
class ProjectIndex:
    """Small, deterministic index of the project shape."""

    root: Path
    engine: EngineName | None
    files: tuple[str, ...]
    scenes: tuple[str, ...]
    scripts: tuple[str, ...]
    assets: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe dictionary."""

        return {
            "root": str(self.root),
            "engine": self.engine,
            "files": list(self.files),
            "scenes": list(self.scenes),
            "scripts": list(self.scripts),
            "assets": list(self.assets),
            "counts": {
                "files": len(self.files),
                "scenes": len(self.scenes),
                "scripts": len(self.scripts),
                "assets": len(self.assets),
            },
        }

    def to_json(self) -> str:
        """Return a pretty JSON representation."""

        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def parse_engine(value: str | None, *, root: Path | str = ".") -> EngineName:
    """Parse a CLI engine argument, using project detection for auto mode."""

    normalized = (value or "auto").strip().lower()
    if normalized in SUPPORTED_ENGINES:
        return cast(EngineName, normalized)

    if normalized in {"auto", "detect"}:
        detection = detect_engine(root)
        if detection.engine is not None:
            return detection.engine
        return "godot"

    allowed = ", ".join(("auto", *SUPPORTED_ENGINES))
    raise ValueError(f"unsupported engine {value!r}; expected one of: {allowed}")


def detect_engine(root: Path | str = ".") -> EngineDetection:
    """Detect Godot or Unity project markers without shelling out."""

    root_path = Path(root).expanduser().resolve()
    reasons: list[str] = []

    godot_markers = [
        root_path / "project.godot",
        root_path / "icon.svg",
    ]
    unity_markers = [
        root_path / "ProjectSettings" / "ProjectVersion.txt",
        root_path / "Assets",
        root_path / "Packages" / "manifest.json",
    ]

    godot_score = sum(1 for marker in godot_markers if marker.exists())
    unity_score = sum(1 for marker in unity_markers if marker.exists())

    if (root_path / "project.godot").exists():
        reasons.append("found project.godot")
    if (root_path / "ProjectSettings" / "ProjectVersion.txt").exists():
        reasons.append("found ProjectSettings/ProjectVersion.txt")
    if (root_path / "Assets").is_dir():
        reasons.append("found Assets directory")
    if (root_path / "Packages" / "manifest.json").exists():
        reasons.append("found Packages/manifest.json")

    if godot_score > 0 and unity_score == 0:
        confidence: Literal["high", "medium"] = "high"
        return EngineDetection(root_path, "godot", confidence, tuple(reasons))

    if unity_score >= 2 and godot_score == 0:
        return EngineDetection(root_path, "unity", "high", tuple(reasons))

    if unity_score == 1 and godot_score == 0:
        return EngineDetection(root_path, "unity", "low", tuple(reasons))

    if godot_score > 0 and unity_score > 0:
        return EngineDetection(root_path, None, "ambiguous", tuple(reasons))

    return EngineDetection(root_path, None, "none", ("no supported engine markers found",))


def init_game_studio(
    root: Path | str = ".",
    *,
    engine: EngineName = "godot",
    overwrite: bool = False,
) -> GameStudioInitResult:
    """Write a reviewable VS Code scaffold into a game project."""

    root_path = Path(root).expanduser().resolve()
    root_path.mkdir(parents=True, exist_ok=True)

    files_written: list[Path] = []
    files_skipped: list[Path] = []

    for relative_path, file_content in vscode_templates(engine).items():
        destination = root_path / relative_path
        if destination.exists() and not overwrite:
            files_skipped.append(destination)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(file_content, encoding="utf-8")
        files_written.append(destination)

    return GameStudioInitResult(
        root=root_path,
        engine=engine,
        files_written=tuple(files_written),
        files_skipped=tuple(files_skipped),
    )


def index_project(root: Path | str = ".", *, max_files: int = 400) -> ProjectIndex:
    """Build a compact file index suitable for docs, prompts, and agent context."""

    root_path = Path(root).expanduser().resolve()
    detection = detect_engine(root_path)
    files = tuple(
        _relative_path(root_path, path)
        for path in _iter_project_files(root_path, max_files)
    )

    scenes = tuple(path for path in files if Path(path).suffix.lower() in SCENE_SUFFIXES)
    scripts = tuple(path for path in files if Path(path).suffix.lower() in SCRIPT_SUFFIXES)
    assets = tuple(path for path in files if Path(path).suffix.lower() in ASSET_SUFFIXES)

    return ProjectIndex(
        root=root_path,
        engine=detection.engine,
        files=files,
        scenes=scenes,
        scripts=scripts,
        assets=assets,
    )


def studio_doctor_lines(root: Path | str = ".") -> tuple[str, ...]:
    """Return diagnostic lines for a local game project setup."""

    root_path = Path(root).expanduser().resolve()
    detection = detect_engine(root_path)
    lines: list[str] = []

    if detection.engine is None:
        lines.append(f"warn engine: {detection.confidence}")
    else:
        lines.append(f"ok engine: {detection.engine} ({detection.confidence})")

    lines.extend(f"info marker: {reason}" for reason in detection.reasons)

    godot_path = shutil.which("godot") or shutil.which("godot4")
    unity_editor = os.environ.get("UNITY_EDITOR") or shutil.which("unity")

    if detection.engine in {None, "godot"}:
        if godot_path:
            lines.append(f"ok godot-cli: {godot_path}")
        else:
            lines.append("warn godot-cli: not found on PATH")

    if detection.engine in {None, "unity"}:
        if unity_editor:
            lines.append(f"ok unity-cli: {unity_editor}")
        else:
            lines.append("warn unity-cli: set UNITY_EDITOR to your Unity executable path")

    index = index_project(root_path)
    lines.append(
        "info index: "
        f"files={len(index.files)} scenes={len(index.scenes)} "
        f"scripts={len(index.scripts)} assets={len(index.assets)}"
    )

    return tuple(lines)


def vscode_templates(engine: EngineName) -> dict[str, str]:
    """Return VS Code workspace templates for the selected engine."""

    if engine == "godot":
        return _godot_templates()
    return _unity_templates()


def _buddy_workspace_tasks() -> list[dict[str, object]]:
    return [
        {
            "label": "Buddy: Initialize Playground",
            "type": "shell",
            "command": "buddy-workspace init .",
            "problemMatcher": [],
        },
        {
            "label": "Buddy: Playground Status",
            "type": "shell",
            "command": "buddy-workspace status .",
            "problemMatcher": [],
        },
        {
            "label": "Buddy: Draft Code Task",
            "type": "shell",
            "command": "buddy-workspace code-task . \"New code task\" \"Describe the task here.\"",
            "problemMatcher": [],
        },
        {
            "label": "Buddy: Draft Art Request",
            "type": "shell",
            "command": "buddy-workspace art-request . \"New art request\" \"Describe the asset here.\"",
            "problemMatcher": [],
        },
    ]


def _godot_templates() -> dict[str, str]:
    extensions = {
        "recommendations": [
            "geequlim.godot-tools",
            "ms-dotnettools.csharp",
            "editorconfig.editorconfig",
            "eamodio.gitlens",
        ]
    }
    settings = {
        "editor.formatOnSave": True,
        "files.exclude": {
            "**/.godot": True,
            "**/imported": True,
            "**/.import": True,
        },
        "godot_tools.editor_path": "godot",
    }
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Godot: Run Game",
                "type": "shell",
                "command": "godot --path .",
                "problemMatcher": [],
            },
            {
                "label": "Godot: Headless Smoke",
                "type": "shell",
                "command": "godot --headless --path . --quit",
                "problemMatcher": [],
            },
            {
                "label": "Buddy: Index Game Project",
                "type": "shell",
                "command": "buddy game-studio index .",
                "problemMatcher": [],
            },
            *_buddy_workspace_tasks(),
        ],
    }
    launch = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Godot: Launch Game",
                "type": "godot",
                "request": "launch",
                "project": "${workspaceFolder}",
            }
        ],
    }
    return {
        ".vscode/extensions.json": _json(extensions),
        ".vscode/settings.json": _json(settings),
        ".vscode/tasks.json": _json(tasks),
        ".vscode/launch.json": _json(launch),
        ".vscode/BUDDY_GAME_STUDIO.md": _workspace_notes("godot"),
    }


def _unity_templates() -> dict[str, str]:
    extensions = {
        "recommendations": [
            "visualstudiotoolsforunity.vstuc",
            "ms-dotnettools.csharp",
            "ms-dotnettools.csdevkit",
            "editorconfig.editorconfig",
            "eamodio.gitlens",
        ]
    }
    settings = {
        "editor.formatOnSave": True,
        "files.exclude": {
            "**/Library": True,
            "**/Temp": True,
            "**/Obj": True,
            "**/Build": True,
            "**/Builds": True,
            "**/Logs": True,
            "**/UserSettings": True,
        },
    }
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Unity: EditMode Tests",
                "type": "shell",
                "command": (
                    "${env:UNITY_EDITOR} -batchmode -projectPath . "
                    "-runTests -testPlatform editmode -quit"
                ),
                "problemMatcher": [],
            },
            {
                "label": "Unity: Open Project",
                "type": "shell",
                "command": "${env:UNITY_EDITOR} -projectPath .",
                "problemMatcher": [],
            },
            {
                "label": "Buddy: Index Game Project",
                "type": "shell",
                "command": "buddy game-studio index .",
                "problemMatcher": [],
            },
            *_buddy_workspace_tasks(),
        ],
    }
    launch = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Unity: Attach Debugger",
                "type": "vstuc",
                "request": "attach",
            }
        ],
    }
    return {
        ".vscode/extensions.json": _json(extensions),
        ".vscode/settings.json": _json(settings),
        ".vscode/tasks.json": _json(tasks),
        ".vscode/launch.json": _json(launch),
        ".vscode/BUDDY_GAME_STUDIO.md": _workspace_notes("unity"),
    }


def _workspace_notes(engine: EngineName) -> str:
    if engine == "godot":
        run_command = "Run **Terminal > Run Task > Godot: Run Game**."
        editor_note = (
            "Keep Godot open for scenes, inspectors, animation, tilemaps, and exports."
        )
    else:
        run_command = (
            "Set `UNITY_EDITOR`, then run "
            "**Terminal > Run Task > Unity: EditMode Tests**."
        )
        editor_note = "Keep Unity open for scenes, prefabs, inspectors, animator, and builds."

    return (
        "# Buddy Game Studio\n\n"
        "This workspace turns VS Code into the development cockpit while the game engine "
        "remains the source of truth for runtime/editor behavior.\n\n"
        f"- Engine: `{engine}`\n"
        f"- {editor_note}\n"
        "- Use VS Code for code, Git, docs, tasks, indexing, and guarded Buddy prompts.\n"
        f"- {run_command}\n"
        "- Run **Terminal > Run Task > Buddy: Initialize Playground** to create Buddy's "
        "local playground.\n"
        "- Run **Terminal > Run Task > Buddy: Index Game Project** before asking an "
        "agent to edit.\n\n"
        "Guardrail: do not let an agent rewrite imported/cache folders. Review scene "
        "and prefab diffs before committing.\n"
    )


def _iter_project_files(root: Path, max_files: int) -> list[Path]:
    paths: list[Path] = []
    if not root.exists():
        return paths

    for path in sorted(root.rglob("*")):
        if len(paths) >= max_files:
            break
        if not path.is_file():
            continue
        if _is_ignored(root, path):
            continue
        paths.append(path)

    return paths


def _is_ignored(root: Path, path: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    return any(part in IGNORED_DIRECTORIES for part in relative_parts)


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"
