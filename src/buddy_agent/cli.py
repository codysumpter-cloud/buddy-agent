"""Command-line entrypoint for Buddy Agent."""

from __future__ import annotations

import argparse

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
        choices=("doctor", "status"),
        help="Run a scaffold command.",
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
        print("Buddy Agent scaffold doctor: ok")
        return 0

    if args.command == "status":
        print("Buddy Agent scaffold status: initialized")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
