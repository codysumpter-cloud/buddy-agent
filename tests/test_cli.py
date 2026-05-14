from buddy_agent.cli import main


def test_version_command(capsys):
    assert main(["--version"]) == 0
    captured = capsys.readouterr()
    assert "buddy-agent 0.1.0" in captured.out


def test_doctor_command(capsys):
    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "ok runtime" in captured.out
    assert "ok runtime-config" in captured.out
    assert "ok companion-shell" in captured.out
    assert "ok vault-provider" in captured.out
    assert "ok surface-parity" in captured.out


def test_status_command(capsys):
    assert main(["status"]) == 0
    captured = capsys.readouterr()
    assert "Alpha Runtime Plus status: initialized" in captured.out


def test_alpha_command(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("BUDDY_MEMORY_FILE", str(tmp_path / "memory.json"))

    assert main(["alpha"]) == 0
    captured = capsys.readouterr()
    assert "ok default Buddy template valid" in captured.out
    assert "ok BUDDY" in captured.out


def test_app_chat_command(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("BUDDY_MEMORY_FILE", str(tmp_path / "memory.json"))

    assert main(["app-chat", "hello", "bridge", "--surface", "widget"]) == 0
    captured = capsys.readouterr()
    assert "hello bridge" in captured.out
    assert "events=" in captured.out


def test_parity_command(capsys):
    assert main(["parity"]) == 0
    captured = capsys.readouterr()
    assert "ios:" in captured.out
    assert "windows:" in captured.out
    assert "buddy-brain:" in captured.out
    assert "omni-buddy:" in captured.out
    assert "knowledge-vault:" in captured.out
    assert "ok parity" in captured.out
