from importlib import util
from pathlib import Path
from types import ModuleType

from buddy_agent.references import ReferenceRepo


def load_sync_reference_repos() -> ModuleType:
    """Load the reference sync script without requiring scripts to be a package."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "sync_reference_repos.py"
    spec = util.spec_from_file_location("sync_reference_repos", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load sync_reference_repos script")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_sync_dry_run_does_not_create_destination(tmp_path, capsys):
    repo = ReferenceRepo(
        name="Example",
        repository="codysumpter-cloud/example",
        role="test",
        default_branch="main",
    )
    destination = tmp_path / "refs"

    module = load_sync_reference_repos()
    module.sync_repo(destination, repo, dry_run=True)

    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "git clone" in captured.out
    assert not destination.exists()
