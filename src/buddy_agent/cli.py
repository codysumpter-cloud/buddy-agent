"""Command-line entrypoint for Buddy Agent."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .alpha import BuddyAlphaRuntime
from .buddy.generate import default_manifest, write_default_buddy
from .buddy.render_contract import validate_buddy_manifest
from .doctor import doctor_ok, run_doctor
from .game_studio import (
    detect_engine,
    index_project,
    init_game_studio,
    parse_engine,
    studio_doctor_lines,
)
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
from .providers import provider_names
from .receipts import ReceiptWriter
from .runtime import BuddyActionLoopRuntime, RuntimeEngine
from .skills import find_skill_manifest, load_skill_manifests, validate_skill_directory
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
    "skills",
    "providers",
    "receipts",
    "parity",
    "loop",
    "app-chat",
    "agentcraft",
    "train",
    "integrations",
    "game-studio",
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
        "--receipts",
        action="store_true",
        help="Emit local sanitized receipts for supported runtime commands.",
    )
    parser.add_argument("command", nargs="?", choices=COMMANDS, help="Run a Buddy command.")
    parser.add_argument(
        "text",
        nargs="*",
        help=(
            "Text input for chat, memory, recall, skill, skills, train, integration, "
            "or game-studio commands."
        ),
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


def default_skills_path() -> Path:
    """Return the configured public skill manifest path."""
    return Path(os.getenv("BUDDY_SKILLS_PATH", "skills/public"))


def make_runtime(*, emit_receipts: bool = False) -> BuddyAlphaRuntime:
    """Build the alpha runtime with optional receipt emission."""
    writer = ReceiptWriter() if emit_receipts else None
    return BuddyAlphaRuntime(engine=RuntimeEngine(receipt_writer=writer))


def run_smoke_command(*, emit_receipts: bool = False) -> int:
    """Run a small end-to-end CLI/runtime check."""
    writer = ReceiptWriter() if emit_receipts else None
    engine = RuntimeEngine(session_id="smoke", receipt_writer=writer)
    response = engine.receive("hello")
    validate_buddy_manifest(default_manifest())
    print("ok runtime: " + response)
    print("ok buddy-template: default manifest valid")
    return 0


def run_alpha_command(*, emit_receipts: bool = False) -> int:
    """Run the richer Alpha Runtime Plus smoke path."""
    runtime = make_runtime(emit_receipts=emit_receipts)
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


def run_loop_command(parts: list[str], *, emit_receipts: bool = False) -> int:
    """Run Buddy + Lil' Buddy action-loop commands."""
    action = parts[0] if parts else "demo"
    if action != "demo":
        print(f"fail loop: unknown action {action}")
        return 2
    objective = joined_text(parts[1:], fallback="Research context and prepare a useful note.")
    loop = BuddyActionLoopRuntime(receipt_writer=ReceiptWriter() if emit_receipts else None)
    session = loop.start_session(objective)
    print(f"ok loop: Buddy session {session.id}")
    print("Buddy: received mission and delegated safe worker steps")
    safe_steps = (
        ("Summarize Page", "Prepare a concise page summary.", "browser.summarize", "read-only"),
        ("Save Memory", "Stage the useful takeaway as Buddy memory.", "memory.remember", "draft-only"),
        ("Note Draft", "Prepare a note draft from the result.", "note.draft", "draft-only"),
    )
    for title, instruction, action_type, risk in safe_steps:
        delegated = loop.delegate(
            title=title,
            instruction=instruction,
            action_type=action_type,  # type: ignore[arg-type]
            risk=risk,  # type: ignore[arg-type]
        )
        report = loop.complete_action(delegated)
        print(f"Lil' Buddy: {report.summary}")
    gated = loop.delegate(
        title="Review calendar update",
        instruction="Ask Buddy before applying this update.",
        action_type="calendar.create",
        risk="write",
    )
    print(f"Buddy: paused for review on {gated.title} ({gated.risk})")
    print(f"world: {loop.world_state.buddy_status} / {loop.world_state.lil_buddy_status}")
    print(f"receipts: {len(loop.receipts)}")
    return 0


def run_skills_command(parts: list[str]) -> int:
    """Run `buddy skills ...` commands."""
    action = parts[0] if parts else "list"
    root = default_skills_path()
    if action == "list":
        manifests = load_skill_manifests(root)
        for manifest in manifests:
            print(f"{manifest.name}\t{manifest.buddy.risk_class}\t{manifest.description}")
        if not manifests:
            print(f"no skills found under {root}")
        return 0
    if action == "validate":
        problems = validate_skill_directory(root)
        if problems:
            for problem in problems:
                print(f"fail skill: {problem}")
            return 1
        print(f"ok skills: {len(load_skill_manifests(root))} manifests valid")
        return 0
    if action == "inspect":
        if len(parts) < 2:
            print("fail skills inspect: missing skill name")
            return 2
        manifest = find_skill_manifest(root, parts[1])
        if manifest is None:
            print(f"fail skills inspect: unknown skill {parts[1]}")
            return 1
        print(f"name: {manifest.name}")
        print(f"description: {manifest.description}")
        print(f"risk_class: {manifest.buddy.risk_class}")
        print(f"auto_executable: {manifest.buddy.auto_executable}")
        print(f"requires_explicit_approval: {manifest.buddy.requires_explicit_approval}")
        print(f"path: {manifest.path}")
        return 0
    print(f"fail skills: unknown action {action}")
    return 2


def run_providers_command(parts: list[str]) -> int:
    """Run `buddy providers ...` commands."""
    action = parts[0] if parts else "list"
    if action != "list":
        print(f"fail providers: unknown action {action}")
        return 2
    selected = os.getenv("BUDDY_PROVIDER", "local").strip().lower() or "local"
    for name in provider_names():
        suffix = " (selected)" if name == selected else ""
        print(f"{name}{suffix}")
    return 0


def run_receipts_command(parts: list[str]) -> int:
    """Run `buddy receipts ...` commands."""
    action = parts[0] if parts else "path"
    if action != "path":
        print(f"fail receipts: unknown action {action}")
        return 2
    print(ReceiptWriter().path())
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
        print(runtime.describe(integration_id).message)
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
        result = runtime.run(integration_id, parts[2], path=parts[3] if len(parts) > 3 else None)
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
            AgentCraftEvent("mission_start", {"name": "Buddy Agent smoke", "prompt": "redacted smoke event"}),
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
        print(f"state_path={store.path}")
        for line in engine.summary_lines(result.state):
            print(line)
        return 0
    print("Usage: buddy train [status|reward <action>|reset]")
    return 2


def run_game_studio_command(parts: list[str]) -> int:
    """Run VS Code + Godot/Unity workspace helper commands."""
    subcommand = parts[0] if parts else "doctor"
    project_path = parts[1] if len(parts) > 1 else "."
    if subcommand == "doctor":
        for line in studio_doctor_lines(project_path):
            print(line)
        return 0
    if subcommand == "detect":
        detection = detect_engine(project_path)
        engine = detection.engine or "none"
        print(f"ok game-studio: engine={engine} confidence={detection.confidence}")
        for reason in detection.reasons:
            print(f"info marker: {reason}")
        return 0 if detection.engine is not None else 1
    if subcommand == "init":
        engine_arg = parts[2] if len(parts) > 2 else "auto"
        try:
            engine = parse_engine(engine_arg, root=project_path)
        except ValueError as error:
            print(f"fail game-studio: {error}")
            return 2
        for line in init_game_studio(project_path, engine=engine).summary_lines():
            print(line)
        return 0
    if subcommand == "index":
        print(index_project(project_path).to_json())
        return 0
    print("Usage: buddy game-studio [doctor|detect|init|index] [project-path] [engine]")
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
        return run_smoke_command(emit_receipts=args.receipts)
    if args.command == "alpha":
        return run_alpha_command(emit_receipts=args.receipts)
    if args.command == "parity":
        return run_parity_command()
    if args.command == "loop":
        return run_loop_command(args.text, emit_receipts=args.receipts)
    if args.command == "skills":
        return run_skills_command(args.text)
    if args.command == "providers":
        return run_providers_command(args.text)
    if args.command == "receipts":
        return run_receipts_command(args.text)
    if args.command == "integrations":
        return run_integrations_command(args.text)
    if args.command == "game-studio":
        return run_game_studio_command(args.text)
    if args.command == "agentcraft":
        return run_agentcraft_command(args.text)
    if args.command == "train":
        return run_train_command(args.text, state_path=args.state)
    runtime = make_runtime(emit_receipts=args.receipts)
    if args.command == "chat":
        result = runtime.chat(joined_text(args.text))
    elif args.command == "remember":
        result = runtime.remember(joined_text(args.text))
    elif args.command == "recall":
        result = runtime.recall(joined_text(args.text))
    elif args.command == "skill":
        result = runtime.run_skill(args.skill, joined_text(args.text))
    elif args.command == "app-chat":
        result = runtime.route_app_chat(joined_text(args.text), surface=str(args.surface))
    else:
        parser.print_help()
        return 0
    print(result.message)
    if result.detail:
        print(result.detail)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
