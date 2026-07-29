"""CLI for approval-bound git worktree execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from buddy_agent.tasks import TaskStore

from .worktree import CommandSpec, GitWorktreeExecutor, WorktreeExecutionError, WorktreeRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="buddy-exec",
        description="Run a reviewed command plan in a dedicated git worktree.",
    )
    parser.add_argument("--tasks-dir", type=Path, help="Override the persistent Buddy task store.")
    parser.add_argument("--worktree-root", type=Path, help="Override worktree storage.")
    parser.add_argument("--evidence-root", type=Path, help="Override execution evidence storage.")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="Execute a reviewed JSON command plan.")
    run.add_argument("task_id")
    run.add_argument("--repository", type=Path, default=Path.cwd())
    run.add_argument("--plan", type=Path, required=True)

    cleanup = commands.add_parser("cleanup", help="Remove a known Buddy worktree.")
    cleanup.add_argument("task_id")
    cleanup.add_argument("--repository", type=Path, default=Path.cwd())
    cleanup.add_argument("--delete-branch", action="store_true")
    return parser


def _load_plan(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorktreeExecutionError(f"execution plan is unreadable: {path}") from error
    if not isinstance(value, dict):
        raise WorktreeExecutionError("execution plan must be a JSON object")
    return value


def _request(task_id: str, repository: Path, plan: dict[str, Any]) -> WorktreeRequest:
    raw_commands = plan.get("commands")
    if not isinstance(raw_commands, list):
        raise WorktreeExecutionError("execution plan commands must be an array")
    commands: list[CommandSpec] = []
    for index, raw in enumerate(raw_commands, start=1):
        if not isinstance(raw, dict):
            raise WorktreeExecutionError(f"command {index} must be an object")
        argv = raw.get("argv")
        if not isinstance(argv, list) or any(not isinstance(item, str) for item in argv):
            raise WorktreeExecutionError(f"command {index} argv must be an array of strings")
        cwd = raw.get("cwd", ".")
        timeout = raw.get("timeout_seconds", 900)
        if not isinstance(cwd, str) or not isinstance(timeout, int):
            raise WorktreeExecutionError(f"command {index} has invalid cwd or timeout")
        commands.append(CommandSpec(argv=tuple(argv), cwd=cwd, timeout_seconds=timeout))
    base_ref = plan.get("base_ref", "HEAD")
    branch_name = plan.get("branch_name")
    keep_worktree = plan.get("keep_worktree", True)
    if not isinstance(base_ref, str):
        raise WorktreeExecutionError("base_ref must be a string")
    if branch_name is not None and not isinstance(branch_name, str):
        raise WorktreeExecutionError("branch_name must be a string")
    if not isinstance(keep_worktree, bool):
        raise WorktreeExecutionError("keep_worktree must be a boolean")
    return WorktreeRequest(
        task_id=task_id,
        repository=repository,
        commands=tuple(commands),
        base_ref=base_ref,
        branch_name=branch_name,
        keep_worktree=keep_worktree,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    executor = GitWorktreeExecutor(
        TaskStore(args.tasks_dir),
        worktree_root=args.worktree_root,
        evidence_root=args.evidence_root,
    )
    try:
        if args.command == "run":
            request = _request(args.task_id, args.repository, _load_plan(args.plan))
            evidence = executor.execute(request)
            print(json.dumps(evidence.to_dict(), indent=2, sort_keys=True))
            return 0 if evidence.status == "completed" else 1
        executor.cleanup(
            args.repository,
            args.task_id,
            delete_branch=args.delete_branch,
        )
        print(json.dumps({"ok": True, "task_id": args.task_id, "removed": True}, sort_keys=True))
        return 0
    except WorktreeExecutionError as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
