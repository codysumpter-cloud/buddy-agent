"""Local CLI demo for Buddy delegating to one Lil' Buddy."""

from __future__ import annotations

import argparse
import json

from .orchestrator import BuddyOrchestrator


def build_parser() -> argparse.ArgumentParser:
    """Build the local demo parser."""
    parser = argparse.ArgumentParser(
        prog="buddy-demo",
        description="Run a local Buddy + Lil' Buddy orchestration demo.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Prompt to route through Buddy -> Lil Buddy -> Buddy Review.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the local demo and print the orchestration trace as JSON."""
    args = build_parser().parse_args(argv)
    prompt = " ".join(args.prompt).strip() or "Draft a safe project note."
    trace = BuddyOrchestrator().run(prompt)
    print(json.dumps(trace, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
