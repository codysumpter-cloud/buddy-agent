"""Command-line entrypoint for Buddy Agent."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .alpha import BuddyAlphaRuntime
from .buddy.generate import default_manifest, write_default_buddy
from .buddy.render_contract import validate_buddy_manifest
from .doctor import doctor_ok, run_doctor
from .metadata import PROJECT_NAME, VERSION
from .parity import parity_summary_lines, validate_required_surface_parity
from .providers import provider_names
from .receipts import ReceiptWriter
from .runtime import BuddyActionLoopRuntime, RuntimeEngine
from .skills import find_skill_manifest, load_skill_manifests, validate_skill_directory

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
        "--receipts",
        action="store_true",
        help="Emit local sanitized receipts for supported runtime commands.",
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
        help="Text input for chat, memory, recall, skill, or nested commands.",
    )
    parser.add_argument(
        "--output",
        default="generated_buddies/default-buddy",
        help="Output directory for `buddy generate`.",
    )
    parser.add_argument("--skill", default="summarize", help="Skill name for `buddy skill`.")
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
    """Run the richer Alpha Runtime smoke path."""
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
        return 1

    objective = joined_text(parts[1:], fallback="Research the current context and prepare a useful note.")
    loop = BuddyActionLoopRuntime(receipt_writer=ReceiptWriter() if emit_receipts else None)
    session = loop.start_session(objective)
    print(f"ok loop: Buddy session {session.id}")
    print("Buddy: received mission and delegated safe worker steps")

    safe_steps = [
        ("Summarize Page", "Prepare a concise page summary.", "browser.summarize", "read-only"),
        ("Save Memory", "Stage the useful takeaway as Buddy memory.", "memory.remember", "draft-only"),
        ("Note Draft", "Prepare a note draft from the result.", "note.draft", "draft-only"),
    ]
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
            return 1
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
    return 1


def run_providers_command(parts: list[str]) -> int:
    """Run `buddy providers ...` commands."""
    action = parts[0] if parts else "list"
    if action != "list":
        print(f"fail providers: unknown action {action}")
        return 1
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
        return 1
    print(ReceiptWriter().path())
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

    if args.command == "chat":
        result = make_runtime(emit_receipts=args.receipts).chat(joined_text(args.text))
        print(result.message)
        if result.detail:
            print(result.detail)
        return 0 if result.ok else 1

    if args.command == "remember":
        result = make_runtime(emit_receipts=args.receipts).remember(joined_text(args.text))
        print(result.message)
        print(result.detail)
        return 0 if result.ok else 1

    if args.command == "recall":
        result = make_runtime(emit_receipts=args.receipts).recall(joined_text(args.text))
        print(result.message)
        return 0 if result.ok else 1

    if args.command == "skill":
        result = make_runtime(emit_receipts=args.receipts).run_skill(
            args.skill, joined_text(args.text)
        )
        print(result.message)
        return 0 if result.ok else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
