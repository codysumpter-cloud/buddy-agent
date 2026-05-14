from buddy_agent.references import ReferenceRepo
from scripts.sync_reference_repos import sync_repo


def test_reference_sync_dry_run_does_not_create_destination(tmp_path, capsys):
    repo = ReferenceRepo(
        name="Example",
        repository="codysumpter-cloud/example",
        role="test",
        default_branch="main",
    )
    destination = tmp_path / "refs"

    sync_repo(destination, repo, dry_run=True)

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "git clone" in captured.out
    assert not destination.exists()
