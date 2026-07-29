from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from buddy_agent.execution import (
    CommandSpec,
    GitWorktreeExecutor,
    WorktreeExecutionError,
    WorktreeRequest,
)
from buddy_agent.execution.cli import main as execution_cli
from buddy_agent.tasks import TaskRuntime, TaskStore


def git(repository: Path, *argv: str) -> str:
    result = subprocess.run(
        ("git", "-C", str(repository), *argv),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Buddy Test")
    git(root, "config", "user.email", "buddy@example.invalid")
    (root / "README.md").write_text("# Example\n", encoding="utf-8")
    (root / "write_file.py").write_text(
        "from pathlib import Path\n"
        "import os\n"
        "Path('generated.txt').write_text('generated\\n')\n"
        "print(os.environ.get('TOP_SECRET', 'missing'))\n",
        encoding="utf-8",
    )
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    return root


def running_task(tmp_path: Path, root: Path, *, approved: bool = True) -> tuple[TaskStore, str]:
    store = TaskStore(tmp_path / "tasks")
    runtime = TaskRuntime(store)
    task = runtime.create("Modify the fixture", risk="repo-mutation", project_root=root)
    runtime.plan(task.id, ["Run reviewed fixture", "Verify worktree diff"])
    if approved:
        runtime.respond_approval(task.id, approved=True, decided_by="test operator")
        runtime.start(task.id)
    return store, task.id


def executor(tmp_path: Path, store: TaskStore) -> GitWorktreeExecutor:
    return GitWorktreeExecutor(
        store,
        worktree_root=tmp_path / "worktrees",
        evidence_root=tmp_path / "evidence",
    )


def test_executes_in_dedicated_worktree_and_preserves_source_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = repository(tmp_path)
    store, task_id = running_task(tmp_path, root)
    selected = executor(tmp_path, store)
    monkeypatch.setenv("TOP_SECRET", "must-not-be-inherited")

    evidence = selected.execute(
        WorktreeRequest(
            task_id=task_id,
            repository=root,
            commands=(
                CommandSpec((Path(sys.executable).name, "write_file.py"), timeout_seconds=30),
                CommandSpec(("git", "status", "--short"), timeout_seconds=30),
            ),
        )
    )

    assert evidence.status == "completed"
    assert evidence.capabilities["repository_worktree_isolation"] is True
    assert evidence.capabilities["host_filesystem_isolation"] is False
    worktree = Path(evidence.worktree)
    assert (worktree / "generated.txt").read_text(encoding="utf-8") == "generated\n"
    assert not (root / "generated.txt").exists()
    assert "generated.txt" in Path(evidence.git_status_path).read_text(encoding="utf-8")
    first_stdout = Path(evidence.commands[0].stdout_path).read_text(encoding="utf-8")
    assert first_stdout.strip() == "missing"
    assert "must-not-be-inherited" not in json.dumps(evidence.to_dict())
    assert Path(selected.evidence_root / task_id / "execution-evidence.json").is_file()


def test_refuses_unapproved_or_non_running_tasks(tmp_path: Path) -> None:
    root = repository(tmp_path)
    store, task_id = running_task(tmp_path, root, approved=False)
    selected = executor(tmp_path, store)
    request = WorktreeRequest(
        task_id=task_id,
        repository=root,
        commands=(CommandSpec(("git", "status", "--short")),),
    )
    with pytest.raises(WorktreeExecutionError, match="must be running"):
        selected.prepare(request)


def test_refuses_shells_write_git_commands_and_cwd_escape(tmp_path: Path) -> None:
    root = repository(tmp_path)
    store, task_id = running_task(tmp_path, root)
    selected = executor(tmp_path, store)

    for spec, message in (
        (CommandSpec(("bash", "-lc", "echo unsafe")), "not allowlisted"),
        (CommandSpec(("git", "push", "origin", "HEAD")), "read-only execution allowlist"),
        (CommandSpec(("git", "status"), cwd="../"), "escapes the worktree"),
    ):
        request = WorktreeRequest(task_id=task_id, repository=root, commands=(spec,))
        if spec.cwd == "../":
            worktree, _, _ = selected.prepare(request)
            assert worktree.is_dir()
            with pytest.raises(WorktreeExecutionError, match=message):
                selected.execute(request)
            selected.cleanup(root, task_id)
        else:
            evidence = selected.execute(request)
            assert evidence.status == "failed"
            assert evidence.error is not None and message in evidence.error
            selected.cleanup(root, task_id)


def test_cleanup_removes_worktree_but_keeps_branch_by_default(tmp_path: Path) -> None:
    root = repository(tmp_path)
    store, task_id = running_task(tmp_path, root)
    selected = executor(tmp_path, store)
    request = WorktreeRequest(
        task_id=task_id,
        repository=root,
        commands=(CommandSpec(("git", "status", "--short")),),
    )
    evidence = selected.execute(request)
    worktree = Path(evidence.worktree)
    selected.cleanup(root, task_id)
    assert not worktree.exists()
    assert git(root, "show-ref", "--verify", f"refs/heads/buddy/{task_id}")


def test_cli_runs_reviewed_json_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = repository(tmp_path)
    store, task_id = running_task(tmp_path, root)
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "commands": [{"argv": ["git", "status", "--short"], "timeout_seconds": 30}],
                "keep_worktree": True,
            }
        ),
        encoding="utf-8",
    )
    code = execution_cli(
        [
            "--tasks-dir",
            str(store.directory),
            "--worktree-root",
            str(tmp_path / "cli-worktrees"),
            "--evidence-root",
            str(tmp_path / "cli-evidence"),
            "run",
            task_id,
            "--repository",
            str(root),
            "--plan",
            str(plan),
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["task_id"] == task_id
