"""Command line surface for Buddy's readiness and evidence contracts."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .checkpoint import InMemoryCheckpointAdapter, run_checkpoint_smoke
from .local_container import LocalContainerSandboxProvider
from .sandbox import (
    PROFILES,
    PolicyOnlySandboxProvider,
    SandboxCapabilities,
    SandboxProvider,
    profile,
)
from .security import SecurityFinding, evaluate_security_gate


def provider(name: str, workspace: Path | None = None) -> SandboxProvider:
    if name == "local-container":
        return LocalContainerSandboxProvider(workspace or Path.cwd())
    capabilities = {
        "codex": SandboxCapabilities(name, True, True, True, True, False, True, True),
        "github-runner": SandboxCapabilities(name, True, True, True, True, True, False, True),
        "local-process": SandboxCapabilities(name, False, False, False, True, False, False, True),
    }
    try:
        return PolicyOnlySandboxProvider(capabilities[name])
    except KeyError as error:
        raise ValueError(f"unknown sandbox provider: {name}") from error


def run_sandbox(parts: list[str]) -> int:
    action = parts[0] if parts else "profiles"
    if action == "profiles":
        print(json.dumps({name: asdict(value) for name, value in PROFILES.items()}, indent=2))
        return 0
    if action == "plan":
        if len(parts) < 3:
            print("Usage: buddy-readiness sandbox plan <provider> <profile>")
            return 2
        result = provider(parts[1]).plan(profile(parts[2]))
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.executable else 1
    if action == "self-test":
        if len(parts) < 2 or parts[1] != "local-container":
            print("Usage: buddy-readiness sandbox self-test local-container [workspace]")
            return 2
        workspace = Path(parts[2]) if len(parts) > 2 else Path.cwd()
        result = LocalContainerSandboxProvider(workspace).self_test()
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.ok else 1
    print(
        "Usage: buddy-readiness sandbox "
        "[profiles|plan <provider> <profile>|self-test local-container [workspace]]"
    )
    return 2


def run_security(parts: list[str]) -> int:
    if len(parts) < 2 or parts[0] != "gate":
        print("Usage: buddy-readiness security gate <findings.json>")
        return 2
    payload = json.loads(Path(parts[1]).read_text(encoding="utf-8"))
    findings = [SecurityFinding(**item) for item in payload.get("findings", [])]
    result = evaluate_security_gate(findings, set(payload.get("checks_run", [])))
    print(json.dumps(result.to_dict(), indent=2))
    return {"pass": 0, "review": 1, "block": 2}[result.decision]


def run_checkpoint(parts: list[str]) -> int:
    if parts and parts[0] != "smoke":
        print("Usage: buddy-readiness checkpoint smoke")
        return 2
    result = run_checkpoint_smoke(InMemoryCheckpointAdapter())
    print(json.dumps({**asdict(result), "ok": result.ok}, indent=2))
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="buddy-readiness", description="Buddy Agent Readiness Layer contracts."
    )
    parser.add_argument("command", choices=("sandbox", "security", "checkpoint"))
    parser.add_argument("args", nargs="*")
    selected = parser.parse_args(argv)
    if selected.command == "sandbox":
        return run_sandbox(selected.args)
    if selected.command == "security":
        return run_security(selected.args)
    return run_checkpoint(selected.args)


if __name__ == "__main__":
    raise SystemExit(main())
