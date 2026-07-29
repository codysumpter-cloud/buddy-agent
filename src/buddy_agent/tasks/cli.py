"""Command-line interface for persistent Buddy task lifecycle state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from buddy_agent.receipts import ReceiptWriter

from .models import TaskRisk
from .runtime import TaskRuntime, TaskTransitionError
from .store import TaskStore, TaskStoreError

RISKS: tuple[TaskRisk, ...] = (
    "read-only",
    "draft-only",
    "write",
    "repo-mutation",
    "destructive",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="buddy-task",
        description="Persistent, approval-gated Buddy task lifecycle.",
    )
    parser.add_argument("--tasks-dir", type=Path, help="Override BUDDY_TASKS_DIR.")
    parser.add_argument("--receipts-dir", type=Path, help="Write sanitized lifecycle receipts here.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a task without inventing a plan.")
    create.add_argument("objective")
    create.add_argument("--risk", choices=RISKS, default="read-only")
    create.add_argument("--project-root", type=Path)

    subparsers.add_parser("list", help="List task records newest-first.")

    status = subparsers.add_parser("status", help="Read one task record.")
    status.add_argument("task_id")

    plan = subparsers.add_parser("plan", help="Attach a reviewable plan.")
    plan.add_argument("task_id")
    plan.add_argument("--step", action="append", required=True)
    plan.add_argument("--verify", action="append", default=[])

    for command in ("approve", "deny"):
        approval = subparsers.add_parser(command, help=f"{command.title()} a pending task.")
        approval.add_argument("task_id")
        approval.add_argument("--by", required=True, dest="decided_by")
        approval.add_argument("--note")

    start = subparsers.add_parser("start", help="Mark an approved/planned task running.")
    start.add_argument("task_id")

    for command in ("step-complete", "step-fail"):
        step = subparsers.add_parser(command, help="Record one worker step result.")
        step.add_argument("task_id")
        step.add_argument("step_id")
        step.add_argument("--detail")
        step.add_argument("--artifact", action="append", default=[])

    complete = subparsers.add_parser("complete", help="Complete after every step is evidenced.")
    complete.add_argument("task_id")
    complete.add_argument("summary")

    fail = subparsers.add_parser("fail", help="Fail a non-terminal task.")
    fail.add_argument("task_id")
    fail.add_argument("reason")

    cancel = subparsers.add_parser("cancel", help="Cancel a non-terminal task.")
    cancel.add_argument("task_id")
    cancel.add_argument("--reason")

    resume = subparsers.add_parser("resume", help="Resume a cancelled or failed task.")
    resume.add_argument("task_id")
    return parser


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = TaskStore(args.tasks_dir)
    writer = ReceiptWriter(args.receipts_dir) if args.receipts_dir else None
    runtime = TaskRuntime(store, writer)
    try:
        if args.command == "create":
            task = runtime.create(
                args.objective,
                risk=args.risk,
                project_root=args.project_root,
            )
        elif args.command == "list":
            _print([task.to_dict() for task in store.list()])
            return 0
        elif args.command == "status":
            task = store.load(args.task_id)
        elif args.command == "plan":
            task = runtime.plan(args.task_id, args.step, verification=args.verify)
        elif args.command in {"approve", "deny"}:
            task = runtime.respond_approval(
                args.task_id,
                approved=args.command == "approve",
                decided_by=args.decided_by,
                note=args.note,
            )
        elif args.command == "start":
            task = runtime.start(args.task_id)
        elif args.command in {"step-complete", "step-fail"}:
            task = runtime.update_step(
                args.task_id,
                args.step_id,
                completed=args.command == "step-complete",
                detail=args.detail,
                artifact_paths=args.artifact,
            )
        elif args.command == "complete":
            task = runtime.complete(args.task_id, args.summary)
        elif args.command == "fail":
            task = runtime.fail(args.task_id, args.reason)
        elif args.command == "cancel":
            task = runtime.cancel(args.task_id, args.reason)
        elif args.command == "resume":
            task = runtime.resume(args.task_id)
        else:
            raise TaskTransitionError(f"unsupported command: {args.command}")
    except (TaskStoreError, TaskTransitionError) as error:
        _print({"ok": False, "error": str(error)})
        return 2
    _print(task.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
