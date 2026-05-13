import json

from buddy_agent.cli import main


def test_version_command(capsys):
    assert main(["--version"]) == 0
    captured = capsys.readouterr()
    assert "buddy-agent 0.1.0" in captured.out


def test_doctor_command(capsys):
    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "ok runtime" in captured.out
    assert "ok vault-provider" in captured.out
    assert "ok surface-parity" in captured.out


def test_status_command(capsys):
    assert main(["status"]) == 0
    captured = capsys.readouterr()
    assert "alpha status: initialized" in captured.out


def test_parity_command(capsys):
    assert main(["parity"]) == 0
    captured = capsys.readouterr()
    assert "ios:" in captured.out
    assert "windows:" in captured.out
    assert "buddy-brain:" in captured.out
    assert "omni-buddy:" in captured.out
    assert "knowledge-vault:" in captured.out
    assert "ok parity" in captured.out


def test_run_command_uses_config_file(tmp_path, capsys):
    config_path = tmp_path / "buddy.json"
    config_path.write_text(
        json.dumps(
            {
                "home": str(tmp_path),
                "memory_path": str(tmp_path / "memory.json"),
                "omni": {"enabled": True, "model": "cli-test"},
            }
        ),
        encoding="utf-8",
    )

    assert main(["--config", str(config_path), "run", "hello"]) == 0
    captured = capsys.readouterr()

    assert "cli-test" in captured.out


def test_app_chat_command_uses_bridge_route(tmp_path, capsys):
    config_path = tmp_path / "buddy.json"
    config_path.write_text(
        json.dumps(
            {
                "home": str(tmp_path),
                "memory_path": str(tmp_path / "memory.json"),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--buddy-id",
            "buddy-1",
            "app-chat",
            "hello",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Buddy local reply" in captured.out
