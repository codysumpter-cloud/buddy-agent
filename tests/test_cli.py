from buddy_agent.cli import main


def test_version_command(capsys):
    assert main(["--version"]) == 0
    captured = capsys.readouterr()
    assert "buddy-agent 0.1.0" in captured.out


def test_doctor_command(capsys):
    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "doctor: ok" in captured.out


def test_status_command(capsys):
    assert main(["status"]) == 0
    captured = capsys.readouterr()
    assert "status: initialized" in captured.out
