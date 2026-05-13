"""Command-line entrypoint for Buddy Agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from .alpha import BuddyAlphaRuntime
from .buddy.generate import default_manifest, write_default_buddy
from .buddy.render_contract import validate_buddy_manifest
from .config import BuddyAgentConfig
from .doctor import doctor_ok, run_doctor
from .entrypoint import BuddyRuntimeEntrypoint
from .metadata import PROJECT_NAME, VERSION
from .parity import parity_summary_lines, validate_required_surface_parity
from .runtime import RuntimeEngine

COMMANDS = (
    "doctor",
    "status",
    "generate",
    "smoke",
    "alpha",
    "chat",
    "remember",
    "recall",
    "skill",
    "parity",
    "run",
    "app-chat",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the Buddy Agent CLI parser."""
    parser = argparse.ArgumentParser(
        prog="buddy",
        description="Buddy Agent alpha runtime.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the Buddy Agent version and exit.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=COMMANDS,
        help="Run a Buddy command.",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text input for chat, memory, recall, app-chat, run, or skill commands.",
    )
    parser.add_argument(
        "--output",
        default="generated_buddies/default-buddy",
        help="Output directory for `buddy generate`.",
    )
    parser.add_argument("--skill", default="summarize", help="Skill name for `buddy skill`.")
    parser.add_argument(
        "--config",
        default="",
        help="Optional JSON config path for `buddy run`, `buddy alpha`, or `buddy app-chat`.",
    )
    parser.add_argument(
        "--buddy-id",
        default="default-buddy",
        help="Buddy id for app bridge commands.",
    )
    return parser


def joined_text(parts: list[str], *, fallback: str = "hello") -> str:
    """Return positional text joined into one prompt."""
    value = " ".join(parts).strip()
    return value or fallback


def configured_runtime(config_path: str) -> BuddyAlphaRuntime:
    """Create a runtime from config path or environment."""
    if config_path:
        return BuddyAlphaRuntime.from_config(BuddyAgentConfig.from_file(config_path))
    return BuddyAlphaRuntime.from_config(BuddyAgentConfig.from_env())


def run_smoke_command() -> int:
    """Run a small end-to-end CLI/runtime check."""
    engine = RuntimeEngine(session_id="smoke")
    response = engine.receive("hello")
    validate_buddy_manifest(default_manifest())
    print("ok runtime: " + response)
    print("ok buddy-template: default manifest valid")
    return 0


def run_alpha_command(config_path: str = "") -> int:
    """Run the richer Alpha Runtime smoke path."""
    runtime = configured_runtime(config_path)
    for result in runtime.smoke():
        status = "ok" if result.ok else "fail"
        detail = f": {result.detail}" if result.detail else ""
        print(f"{status} {result.message}{detail}")
    return 0


def run_parity_command() -> int:
    """Print the cross-surface parity contract summary."""
    problems = validate_required_surface_parity()
    for line in parity_summary_lines():
        print(line)
    if problems:
        for problem in problems:
            print(f"fail parity: {problem}")
        return 1
    print("ok parity: all required surfaces covered")
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
        print("Buddy Agent alpha status: initialized")
        return 0

    if args.command == "generate":
        manifest_path = write_default_buddy(Path(args.output))
        print(f"Generated Buddy template: {manifest_path}")
        return 0

    if args.command == "smoke":
        return run_smoke_command()

    if args.command == "alpha":
        return run_alpha_command(args.config)

    if args.command == "parity":
        return run_parity_command()

    if args.command == "chat":
        result = BuddyAlphaRuntime().chat(joined_text(args.text))
        print(result.message)
        if result.detail:
            print(result.detail)
        return 0 if result.ok else 1

    if args.command == "remember":
        result = BuddyAlphaRuntime().remember(joined_text(args.text))
        print(result.message)
        print(result.detail)
        return 0 if result.ok else 1

    if args.command == "recall":
        result = BuddyAlphaRuntime().recall(joined_text(args.text))
        print(result.message)
        return 0 if result.ok else 1

    if args.command == "skill":
        result = BuddyAlphaRuntime().run_skill(args.skill, joined_text(args.text))
        print(result.message)
        return 0 if result.ok else 1

    if args.command == "run":
        if args.config:
            entrypoint = BuddyRuntimeEntrypoint.from_config_file(args.config)
        else:
            entrypoint = BuddyRuntimeEntrypoint.from_env()
        result = entrypoint.execute("chat", joined_text(args.text))
        print(result.message)
        if result.detail:
            print(result.detail)
        return 0 if result.ok else 1

    if args.command == "app-chat":
        response = configured_runtime(args.config).app_chat(args.buddy_id, joined_text(args.text))
        print(response.message)
        if response.detail:
            print(response.detail)
        return 0 if response.ok else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
