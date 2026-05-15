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


def test_skills_validate_command(capsys):
    assert main(["skills", "validate"]) == 0
    captured = capsys.readouterr()
    assert "ok skills:" in captured.out


def test_skills_list_command(capsys):
    assert main(["skills", "list"]) == 0
    captured = capsys.readouterr()
    assert "caps" in captured.out
    assert "summarize" in captured.out


def test_skills_inspect_command(capsys):
    assert main(["skills", "inspect", "caps"]) == 0
    captured = capsys.readouterr()
    assert "name: caps" in captured.out
    assert "risk_class: draft-only" in captured.out


def test_providers_list_command(capsys):
    assert main(["providers", "list"]) == 0
    captured = capsys.readouterr()
    assert "local" in captured.out


def test_receipts_path_command(capsys):
    assert main(["receipts", "path"]) == 0
    captured = capsys.readouterr()
    assert ".buddy_agent" in captured.out
