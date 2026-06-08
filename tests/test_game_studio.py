from pathlib import Path

from buddy_agent.game_studio import detect_engine, index_project, init_game_studio, parse_engine


def test_detect_engine_prefers_godot_project_marker(tmp_path: Path):
    (tmp_path / "project.godot").write_text("[application]\n", encoding="utf-8")

    detection = detect_engine(tmp_path)

    assert detection.ok is True
    assert detection.engine == "godot"
    assert detection.confidence == "high"


def test_detect_engine_identifies_unity_project(tmp_path: Path):
    (tmp_path / "Assets").mkdir()
    (tmp_path / "ProjectSettings").mkdir()
    (tmp_path / "ProjectSettings" / "ProjectVersion.txt").write_text(
        "m_EditorVersion: 6000.0.0f1\n",
        encoding="utf-8",
    )

    detection = detect_engine(tmp_path)

    assert detection.ok is True
    assert detection.engine == "unity"
    assert detection.confidence == "high"


def test_parse_engine_auto_defaults_to_godot_for_empty_directory(tmp_path: Path):
    assert parse_engine("auto", root=tmp_path) == "godot"


def test_init_game_studio_writes_godot_vscode_workspace(tmp_path: Path):
    result = init_game_studio(tmp_path, engine="godot")

    assert result.engine == "godot"
    assert (tmp_path / ".vscode" / "tasks.json").exists()
    assert (tmp_path / ".vscode" / "settings.json").exists()
    assert (tmp_path / ".vscode" / "BUDDY_GAME_STUDIO.md").exists()

    tasks = (tmp_path / ".vscode" / "tasks.json").read_text(encoding="utf-8")
    assert "Godot: Run Game" in tasks
    assert "Buddy: Index Game Project" in tasks


def test_init_game_studio_does_not_overwrite_existing_files_by_default(tmp_path: Path):
    settings = tmp_path / ".vscode" / "settings.json"
    settings.parent.mkdir()
    settings.write_text('{"custom": true}\n', encoding="utf-8")

    result = init_game_studio(tmp_path, engine="unity")

    assert settings in result.files_skipped
    assert settings.read_text(encoding="utf-8") == '{"custom": true}\n'


def test_index_project_ignores_engine_cache_directories(tmp_path: Path):
    (tmp_path / "project.godot").write_text("[application]\n", encoding="utf-8")
    (tmp_path / "scenes").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".godot").mkdir()
    (tmp_path / "scenes" / "main.tscn").write_text("[gd_scene]\n", encoding="utf-8")
    (tmp_path / "scripts" / "player.gd").write_text("extends Node\n", encoding="utf-8")
    (tmp_path / ".godot" / "cache.bin").write_text("ignore me\n", encoding="utf-8")

    index = index_project(tmp_path)

    assert index.engine == "godot"
    assert "scenes/main.tscn" in index.scenes
    assert "scripts/player.gd" in index.scripts
    assert ".godot/cache.bin" not in index.files
