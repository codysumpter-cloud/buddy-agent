"""Command-line entrypoint for Buddy Agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from .buddy.generate import write_default_buddy
from .doctor import doctor_ok, run_doctor
from .metadata import PROJECT_NAME, VERSION


def build_parser() -> argparse.ArgumentParser:
    """Build the Buddy Agent CLI parser."""
    parser = argparse.ArgumentParser(
        prog="buddy",
        description="Buddy Agent runtime scaffold.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the Buddy Agent version and exit.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("doctor", "status", "generate"),
        help="Run a scaffold command.",
    )
    parser.add_argument(
        "--output",
        default="generated_buddies/default-buddy",
        help="Output directory for `buddy generate`.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Buddy Agent CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"{PROJECT_NAME} {VERSION}")
        return 0

    if args.command == "doctor":
        checks = run_doctor()
        for check in checks:
            status = "ok" if check.ok else "fail"
            print(f"{status} {check.name}: {check.detail}")
        return 0 if doctor_ok(checks) else 1

    if args.command == "status":
        print("Buddy Agent scaffold status: initialized")
        return 0

    if args.command == "generate":
        manifest_path = write_default_buddy(Path(args.output))
        print(f"Generated Buddy template: {manifest_path}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
