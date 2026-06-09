"""Canonical Buddy product spine across app, runtime, and brain repos."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Literal

SurfaceKind = Literal[
    "app-ui",
    "runtime",
    "orchestration",
    "workspace",
    "browser",
    "skill",
    "docs",
]
RiskClass = Literal[
    "read-only",
    "draft-only",
    "write",
    "external-action",
    "destructive",
    "credential",
    "money",
    "repo-mutation",
]


@dataclass(frozen=True)
class ProductRepo:
    """Repository participating in the Buddy product."""

    name: str
    default_branch: str
    owns: tuple[str, ...]


@dataclass(frozen=True)
class ProductSurface:
    """A concrete product surface that already exists or is established by this repo."""

    id: str
    title: str
    kind: SurfaceKind
    owner_repo: str
    paths: tuple[str, ...]
    status: str
    product_role: str


@dataclass(frozen=True)
class ProductFlowStep:
    """One step in the end-to-end Buddy product loop."""

    order: int
    actor: str
    surface_id: str
    action: str
    output: str
    risk: RiskClass


@dataclass(frozen=True)
class ProductSpine:
    """Machine-readable map tying the scattered Buddy systems into one product."""

    version: str
    product: str
    promise: str
    repos: tuple[ProductRepo, ...]
    surfaces: tuple[ProductSurface, ...]
    flow: tuple[ProductFlowStep, ...]
    approval_required: tuple[RiskClass, ...]
    canonical_runtime_artifacts: tuple[str, ...]
    local_project_artifacts: tuple[str, ...]


def buddy_product_spine() -> ProductSpine:
    """Return the canonical Buddy product spine."""

    return ProductSpine(
        version="2026-06-09",
        product="Buddy / BeMore Agent Workspace",
        promise=(
            "One functional product loop: Prismtek Apps owns the user-facing Agent Browser "
            "and .bemore runtime, Buddy Agent owns local runtime and project workspace contracts, "
            "and Buddy Brain owns orchestration, worker dispatch, and policy."
        ),
        repos=(
            ProductRepo(
                name="codysumpter-cloud/prismtek-apps",
                default_branch="main",
                owns=(
                    "iOS/macOS product surfaces",
                    "guarded Agent Browser UI",
                    ".bemore workspace runtime",
                    "receipt/artifact rendering",
                    "linked-account and app-visible settings",
                ),
            ),
            ProductRepo(
                name="codysumpter-cloud/buddy-agent",
                default_branch="main",
                owns=(
                    "local Buddy CLI/runtime",
                    "app-chat bridge seam",
                    "Buddy Playground project workspace",
                    "Game Studio VS Code/Godot/Unity helpers",
                    "integration status and local contracts",
                ),
            ),
            ProductRepo(
                name="codysumpter-cloud/buddy-brain",
                default_branch="master",
                owns=(
                    "operator policy",
                    "workspace dispatch",
                    "browser automation profile",
                    "orchestrator/worker runbooks",
                    "cross-repo ownership boundaries",
                ),
            ),
        ),
        surfaces=(
            ProductSurface(
                id="agent-browser",
                title="Guarded Agent Browser",
                kind="app-ui",
                owner_repo="codysumpter-cloud/prismtek-apps",
                paths=(
                    "apps/bemore-ios-native/BeMoreAgentShell/Views/BuddyAgentBrowserView.swift",
                    "apps/bemore-ios-native/BeMoreAgentShell/WebBrowserService.swift",
                    "docs/BUDDY_ACTION_LOOP_V1.md",
                ),
                status="implemented-app-mvp",
                product_role="Human starts missions, Buddy delegates to Lil' Buddy, and risky actions pause for approval.",
            ),
            ProductSurface(
                id="bemore-workspace-runtime",
                title=".bemore Workspace Runtime",
                kind="workspace",
                owner_repo="codysumpter-cloud/prismtek-apps",
                paths=(
                    "apps/bemore-ios-native/BeMoreAgentShell/BeMoreWorkspaceRuntime.swift",
                    "docs/BUDDY_CAPABILITY_SURFACES.md",
                ),
                status="implemented-app-local-runtime",
                product_role="Persists app-visible skills, artifacts, receipts, memory, session state, and runtime actions.",
            ),
            ProductSurface(
                id="buddy-agent-runtime",
                title="Buddy Agent Runtime",
                kind="runtime",
                owner_repo="codysumpter-cloud/buddy-agent",
                paths=(
                    "src/buddy_agent/cli.py",
                    "src/buddy_agent/alpha.py",
                    "src/buddy_agent/runtime.py",
                ),
                status="runnable-alpha",
                product_role="Provides the local CLI, chat path, memory path, skills, app-chat seam, integrations, and diagnostics.",
            ),
            ProductSurface(
                id="buddy-playground",
                title="Buddy Playground Workspace",
                kind="workspace",
                owner_repo="codysumpter-cloud/buddy-agent",
                paths=(
                    "src/buddy_agent/workspace.py",
                    "src/buddy_agent/cli_workspace.py",
                    "docs/BUDDY_GAME_STUDIO.md",
                ),
                status="implemented-local-project-workspace",
                product_role="Stores reviewable local files, browser notes, code tasks, art briefs, outbox drafts, and receipts before adapters act.",
            ),
            ProductSurface(
                id="game-studio",
                title="Buddy Game Studio",
                kind="runtime",
                owner_repo="codysumpter-cloud/buddy-agent",
                paths=(
                    "src/buddy_agent/game_studio.py",
                    "docs/BUDDY_GAME_STUDIO.md",
                ),
                status="implemented-vscode-cockpit",
                product_role="Turns game repos into inspectable VS Code + Godot/Unity workspaces with Buddy task hooks.",
            ),
            ProductSurface(
                id="workspace-dispatch",
                title="Workspace Dispatch",
                kind="orchestration",
                owner_repo="codysumpter-cloud/buddy-brain",
                paths=(
                    "skills/workspace-dispatch/SKILL.md",
                    "docs/UNIFIED_OPERATOR_APP.md",
                ),
                status="documented-orchestration-contract",
                product_role="Defines the worker task loop, verification rules, retry behavior, and operator ownership boundaries.",
            ),
            ProductSurface(
                id="browser-policy",
                title="Browser Automation Policy",
                kind="browser",
                owner_repo="codysumpter-cloud/buddy-brain",
                paths=(
                    "docs/BROWSER_AUTOMATION_PROFILE.md",
                    "skills/browser-automation/README.md",
                ),
                status="documented-policy-contract",
                product_role="Keeps browser automation opt-in, scoped, auditable, and separate from default chat execution.",
            ),
        ),
        flow=(
            ProductFlowStep(
                order=1,
                actor="Human",
                surface_id="agent-browser",
                action="Enter mission or open/search a page in the guarded Agent Browser.",
                output="BuddyAgentSession intent, current URL, and visible UI context.",
                risk="read-only",
            ),
            ProductFlowStep(
                order=2,
                actor="Buddy Orchestrator",
                surface_id="workspace-dispatch",
                action="Decompose the mission into bounded worker steps with exit criteria.",
                output="Worker plan with approval checkpoints.",
                risk="draft-only",
            ),
            ProductFlowStep(
                order=3,
                actor="Lil' Buddy Worker",
                surface_id="buddy-playground",
                action="Draft browser notes, code tasks, art briefs, files, email/message/calendar outbox items, or receipts.",
                output="Reviewable .buddy/playground artifact.",
                risk="draft-only",
            ),
            ProductFlowStep(
                order=4,
                actor="Buddy Runtime",
                surface_id="buddy-agent-runtime",
                action="Validate local runtime status, integration capability, and app-chat handoff.",
                output="CLI/app bridge result and sanitized status.",
                risk="read-only",
            ),
            ProductFlowStep(
                order=5,
                actor="Prismtek Apps Runtime",
                surface_id="bemore-workspace-runtime",
                action="Promote approved useful outputs into .bemore skills, artifacts, receipts, memory, or session state.",
                output="App-visible BeMoreReceipt and persisted artifact.",
                risk="write",
            ),
            ProductFlowStep(
                order=6,
                actor="External Adapter",
                surface_id="browser-policy",
                action="Only after approval, perform browser/account/calendar/message/email/repo external actions.",
                output="Secret-free receipt and verification status.",
                risk="external-action",
            ),
        ),
        approval_required=(
            "write",
            "external-action",
            "destructive",
            "credential",
            "money",
            "repo-mutation",
        ),
        canonical_runtime_artifacts=(
            ".bemore/soul.md",
            ".bemore/user.md",
            ".bemore/memory.md",
            ".bemore/session.md",
            ".bemore/skills.md",
            ".bemore/registry/skills.json",
            ".bemore/logs/latest-actions.log",
        ),
        local_project_artifacts=(
            ".buddy/playground/manifest.json",
            ".buddy/playground/permissions.json",
            ".buddy/playground/browser/research_notes/",
            ".buddy/playground/code/tasks/",
            ".buddy/playground/art/requests/",
            ".buddy/playground/outbox/email_drafts/",
            ".buddy/playground/outbox/message_drafts/",
            ".buddy/playground/outbox/calendar_drafts/",
            ".buddy/playground/receipts/",
        ),
    )


def product_spine_dict() -> dict[str, object]:
    """Return the product spine as a JSON-ready dictionary."""

    return asdict(buddy_product_spine())


def product_spine_json() -> str:
    """Return the product spine as stable, pretty JSON."""

    return json.dumps(product_spine_dict(), indent=2, sort_keys=True)


def validate_product_spine() -> list[str]:
    """Validate cross-references inside the product spine."""

    spine = buddy_product_spine()
    errors: list[str] = []
    repo_names = {repo.name for repo in spine.repos}
    surface_ids = {surface.id for surface in spine.surfaces}

    for surface in spine.surfaces:
        if surface.owner_repo not in repo_names:
            errors.append(f"surface {surface.id} references unknown repo {surface.owner_repo}")
        if not surface.paths:
            errors.append(f"surface {surface.id} has no source paths")

    for step in spine.flow:
        if step.surface_id not in surface_ids:
            errors.append(f"flow step {step.order} references unknown surface {step.surface_id}")
        if step.risk in spine.approval_required and "approval" not in step.action.lower():
            if step.risk in ("external-action", "destructive", "credential", "money", "repo-mutation"):
                errors.append(f"flow step {step.order} is gated but does not mention approval")

    if len(spine.flow) < 5:
        errors.append("product flow must cover app, orchestrator, worker, runtime, and persistence")

    return errors


def product_spine_summary_lines() -> list[str]:
    """Return human-readable product spine summary lines."""

    spine = buddy_product_spine()
    lines = [
        f"product={spine.product}",
        f"version={spine.version}",
        f"repos={len(spine.repos)} surfaces={len(spine.surfaces)} flow_steps={len(spine.flow)}",
        f"promise={spine.promise}",
        "repos:",
    ]
    lines.extend(f"- {repo.name} ({repo.default_branch}): {', '.join(repo.owns)}" for repo in spine.repos)
    lines.append("surfaces:")
    lines.extend(
        f"- {surface.id}: {surface.status} owned by {surface.owner_repo}"
        for surface in spine.surfaces
    )
    lines.append("flow:")
    lines.extend(
        f"{step.order}. {step.actor} -> {step.surface_id}: {step.action} [{step.risk}]"
        for step in spine.flow
    )
    errors = validate_product_spine()
    lines.append("validation=ok" if not errors else "validation=failed")
    lines.extend(f"error={error}" for error in errors)
    return lines
