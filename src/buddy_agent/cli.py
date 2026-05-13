"""Command-line entrypoint for Buddy Agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from .buddy.generate import default_manifest, write_default_buddy
from .buddy.render_contract import validate_buddy_manifest
from .doctor import doctor_ok, run_doctor
from .metadata import PROJECT_NAME, VERSION
from .runtime import RuntimeEngine


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
        choices=("doctor", "status", "generate", "smoke"),
        help="Run a scaffold command.",
    )
    parser.add_argument(
        "--output",
        default="generated_buddies/default-buddy",
        help="Output directory for `buddy generate`.",
    )
    return parser


def run_smoke_command() -> int:
    """Run a small end-to-end CLI/runtime check."""
    engine = RuntimeEngine(session_id="smoke")
    response = engine.receive("hello")
    validate_buddy_manifest(default_manifest())
    print("ok runtime: " + response)
    print("ok buddy-template: default manifest valid")
    return 0


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

    if args.command == "smoke":
        return run_smoke_command()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
