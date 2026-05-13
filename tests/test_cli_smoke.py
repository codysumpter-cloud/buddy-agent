from buddy_agent.cli import main


def test_smoke_command(capsys):
    assert main(["smoke"]) == 0
    captured = capsys.readouterr()
    assert "ok runtime" in captured.out
    assert "ok buddy-template" in captured.out
