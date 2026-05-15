"""Command-line entrypoint for Buddy Agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from .alpha import BuddyAlphaRuntime
from .buddy.generate import default_manifest, write_default_buddy
from .buddy.render_contract import validate_buddy_manifest
from .doctor import doctor_ok, run_doctor
from .integrations import BuddyIntegrationRuntime, parse_integration_id
from .integrations.agentcraft import (
    AgentCraftBridge,
    AgentCraftConfig,
    AgentCraftEvent,
    parse_event_type,
    parse_payload_json,
)
from .metadata import PROJECT_NAME, VERSION
from .parity import parity_summary_lines, validate_required_surface_parity
from .runtime import RuntimeEngine
from .training import BuddyTrainingEngine, BuddyTrainingStore
from .training.models import parse_training_action

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
    "app-chat",
    "agentcraft",
    "train",
    "integrations",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the Buddy Agent CLI parser."""
    parser = argparse.ArgumentParser(
        prog="buddy",
        description="Buddy Agent Alpha Runtime Plus.",
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
        help="Text input for chat, memory, recall, skill, train, or integration commands.",
    )
    parser.add_argument(
        "--output",
        default="generated_buddies/default-buddy",
        help="Output directory for `buddy generate`.",
    )
    parser.add_argument("--skill", default="summarize", help="Skill name for `buddy skill`.")
    parser.add_argument("--surface", default="local", help="Surface name for `buddy app-chat`.")
    parser.add_argument(
        "--state",
        default=None,
        help="Optional state path for `buddy train` commands.",
    )
    return parser


def joined_text(parts: list[str], *, fallback: str = "hello") -> str:
    """Return positional text joined into one prompt."""
    value = " ".join(parts).strip()
    return value or fallback


def run_smoke_command() -> int:
    """Run a small end-to-end CLI/runtime check."""
    engine = RuntimeEngine(session_id="smoke")
    response = engine.receive("hello")
    validate_buddy_manifest(default_manifest())
    print("ok runtime: " + response)
    print("ok buddy-template: default manifest valid")
    return 0


def run_alpha_command() -> int:
    """Run the richer Alpha Runtime Plus smoke path."""
    runtime = BuddyAlphaRuntime()
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


def run_integrations_command(parts: list[str]) -> int:
    """Run priority integration registry commands."""
    runtime = BuddyIntegrationRuntime()
    subcommand = parts[0] if parts else "list"

    if subcommand == "list":
        for line in runtime.list_targets():
            print(line)
        return 0

    if subcommand == "describe":
        try:
            integration_id = parse_integration_id(parts[1] if len(parts) > 1 else "")
        except ValueError as error:
            print(f"fail integrations: {error}")
            return 2
        result = runtime.describe(integration_id)
        print(result.message)
        return 0

    if subcommand == "run":
        try:
            integration_id = parse_integration_id(parts[1] if len(parts) > 1 else "")
        except ValueError as error:
            print(f"fail integrations: {error}")
            return 2
        if len(parts) < 3:
            print("Usage: buddy integrations run <target> <capability> [path]")
            return 2
        result = runtime.run(
            integration_id,
            parts[2],
            path=parts[3] if len(parts) > 3 else None,
        )
        print(result.message)
        if result.detail:
            print(result.detail)
        return 0 if result.ok else 1

    print("Usage: buddy integrations [list|describe <target>|run <target> <capability>]")
    return 2


def run_agentcraft_command(parts: list[str]) -> int:
    """Run AgentCraft helper commands."""
    subcommand = parts[0] if parts else "doctor"
    bridge = AgentCraftBridge()

    if subcommand == "doctor":
        for line in AgentCraftConfig.from_env().doctor_lines():
            print(line)
        return 0

    if subcommand == "smoke":
        events = (
            AgentCraftEvent("hero_active", {"name": "Buddy Agent smoke"}),
            AgentCraftEvent(
                "mission_start",
                {"name": "Buddy Agent smoke", "prompt": "redacted smoke event"},
            ),
            AgentCraftEvent("hero_idle", {"name": "Buddy Agent smoke"}),
        )
        for event in events:
            print(bridge.emit(event).to_json())
        return 0

    if subcommand == "emit":
        try:
            event_type = parse_event_type(parts[1] if len(parts) > 1 else "")
            payload = parse_payload_json(" ".join(parts[2:]) if len(parts) > 2 else None)
        except ValueError as error:
            print(f"fail agentcraft: {error}")
            return 2
        print(bridge.emit(AgentCraftEvent(event_type, payload)).to_json())
        return 0

    print("Usage: buddy agentcraft [doctor|smoke|emit <event-type> [json-payload]]")
    return 2


def run_train_command(parts: list[str], *, state_path: str | None = None) -> int:
    """Run Buddy Training helper commands."""
    subcommand = parts[0] if parts else "status"
    store = BuddyTrainingStore(Path(state_path).expanduser() if state_path else None)
    engine = BuddyTrainingEngine()

    if subcommand == "status":
        state = store.load()
        for line in engine.summary_lines(state):
            print(line)
        print(f"state_path={store.path}")
        return 0

    if subcommand == "reset":
        state = store.reset()
        print("ok train: reset Buddy Training state")
        print(f"state_path={store.path}")
        for line in engine.summary_lines(state):
            print(line)
        return 0

    if subcommand == "reward":
        try:
            action = parse_training_action(parts[1] if len(parts) > 1 else "")
        except ValueError as error:
            print(f"fail train: {error}")
            return 2

        state = store.load()
        result = engine.apply(state, action)
        store.save(result.state)
        print(
            "ok train: "
            f"action={action} xp=+{result.reward.xp} sparks=+{result.reward.sparks} "
            f"snacks=+{result.reward.snacks} levels=+{result.levels_gained}"
        )
        if result.new_achievements:
            print("new achievements: " + ", ".join(result.new_achievements))
        if result.new_cosmetics:
            print("new cosmetics: " + ", ".join(result.new_cosmetics))
        print(f"state_path={store.path}")
        for line in engine.summary_lines(result.state):
            print(line)

        bridge = AgentCraftBridge()
        bridge.emit(
            AgentCraftEvent(
                "mission_start",
                {
                    "name": "Buddy Training reward",
                    "trainingAction": action,
                    "xp": result.reward.xp,
                },
            )
        )
        bridge.emit(
            AgentCraftEvent(
                "hero_idle",
                {
                    "name": "Buddy Training",
                    "level": result.state.level,
                    "evolution": result.state.evolution,
                },
            )
        )
        return 0

    print("Usage: buddy train [status|reward <action>|reset]")
    return 2


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
        print("Buddy Agent Alpha Runtime Plus status: initialized")
        return 0

    if args.command == "generate":
        manifest_path = write_default_buddy(Path(args.output))
        print(f"Generated Buddy template: {manifest_path}")
        return 0

    if args.command == "smoke":
        return run_smoke_command()

    if args.command == "alpha":
        return run_alpha_command()

    if args.command == "parity":
        return run_parity_command()

    if args.command == "integrations":
        return run_integrations_command(args.text)

    if args.command == "agentcraft":
        return run_agentcraft_command(args.text)

    if args.command == "train":
        return run_train_command(args.text, state_path=args.state)

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

    if args.command == "app-chat":
        result = BuddyAlphaRuntime().route_app_chat(
            joined_text(args.text),
            surface=str(args.surface),
        )
        print(result.message)
        if result.detail:
            print(result.detail)
        return 0 if result.ok else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
