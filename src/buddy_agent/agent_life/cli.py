"""CLI for the Buddy Agent Agent Life host."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from buddy_agent.tasks.store import TaskStore

from .runtime import AgentLifeError
from .service import AgentLifeService


def _default_state() -> Path:
    return Path(os.getenv("BUDDY_AGENT_LIFE_STATE", "~/.buddy_agent/agent-life/state.json")).expanduser()


def _default_outbox() -> Path:
    return Path(os.getenv("BUDDY_AGENT_LIFE_OUTBOX", "~/.buddy_agent/agent-life/outbox")).expanduser()


def _evidence(value: str) -> dict[str, str]:
    evidence_type, separator, reference = value.partition("=")
    if not separator or not evidence_type.strip() or not reference.strip():
        raise argparse.ArgumentTypeError("evidence must use type=reference")
    return {"type": evidence_type.strip(), "ref": reference.strip()}


def _service(args: argparse.Namespace) -> AgentLifeService:
    return AgentLifeService.from_paths(args.profile, args.state, args.outbox)


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded, provenance-backed BUAP Agent Life state.")
    parser.add_argument("--profile", type=Path, required=True, help="Compiled .buddy/life-profile.json")
    parser.add_argument("--state", type=Path, default=_default_state(), help="Atomic host state JSON path")
    parser.add_argument("--outbox", type=Path, default=_default_outbox(), help="Knowledge Vault raw event outbox")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("status", help="Show current bounded developmental state")

    preference = commands.add_parser("preference", help="Explain one learned subject preference")
    preference.add_argument("subject_type")
    preference.add_argument("subject_id")

    outcome = commands.add_parser("outcome", help="Apply one externally evidenced outcome")
    outcome.add_argument("--id", required=True)
    outcome.add_argument("--kind", required=True)
    outcome.add_argument("--occurred-at", default=None)
    outcome.add_argument("--subject-type", required=True)
    outcome.add_argument("--subject-id", required=True)
    outcome.add_argument("--reward", required=True, type=float)
    outcome.add_argument("--confidence", type=float, default=1.0)
    outcome.add_argument("--significance", type=float, default=1.0)
    outcome.add_argument("--authority-kind", choices=("human", "host", "verifier"), required=True)
    outcome.add_argument("--authority-id", required=True)
    outcome.add_argument("--evidence", type=_evidence, action="append", required=True)
    outcome.add_argument("--relationship-id", default=None)

    task_outcome = commands.add_parser(
        "task-outcome",
        help="Teach from a terminal Buddy task after an external verifier admits its receipts",
    )
    task_outcome.add_argument("task_id")
    task_outcome.add_argument("--tasks-dir", type=Path, default=None)
    task_outcome.add_argument("--authority-kind", choices=("human", "host", "verifier"), required=True)
    task_outcome.add_argument("--authority-id", required=True)
    task_outcome.add_argument("--evidence", type=_evidence, action="append", required=True)
    task_outcome.add_argument("--subject-id", default=None)

    advance = commands.add_parser("advance", help="Apply time decay and persist state")
    advance.add_argument("hours", type=float)
    advance.add_argument("--now", default=None)

    commands.add_parser("flush", help="Publish interrupted pending memory events")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        service = _service(args)
        if args.command == "status":
            _print(service.status())
        elif args.command == "preference":
            _print(service.runtime.explain_preference({"type": args.subject_type, "id": args.subject_id}))
        elif args.command == "outcome":
            occurred_at = args.occurred_at or datetime.now(UTC).isoformat()
            event: dict[str, Any] = {
                "id": args.id,
                "kind": args.kind,
                "occurred_at": occurred_at,
                "subject": {"type": args.subject_type, "id": args.subject_id},
                "reward": args.reward,
                "confidence": args.confidence,
                "significance": args.significance,
                "authority": {"kind": args.authority_kind, "actor_id": args.authority_id},
                "evidence": args.evidence,
            }
            if args.relationship_id:
                event["relationship_id"] = args.relationship_id
            _print(service.apply_outcome(event))
        elif args.command == "task-outcome":
            task = TaskStore(args.tasks_dir).load(args.task_id)
            _print(
                service.apply_task_outcome(
                    task,
                    authority_kind=args.authority_kind,
                    authority_id=args.authority_id,
                    evidence=args.evidence,
                    subject_id=args.subject_id,
                )
            )
        elif args.command == "advance":
            now = args.now or datetime.now(UTC).isoformat()
            _print(service.advance(args.hours, now))
        elif args.command == "flush":
            _print({"published": [str(path) for path in service.flush_pending()]})
        else:
            parser.error("unknown command")
    except AgentLifeError as error:
        parser.error(str(error))
    return 0
