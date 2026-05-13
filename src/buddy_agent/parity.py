"""Cross-surface parity contracts for Buddy Agent.

Buddy Agent should not import product apps, operator repos, or vault internals directly.
This module keeps the shared capability surface explicit so iOS, Windows,
Buddy Brain, Omni Buddy, and Knowledge Vault can move independently while
Buddy Agent keeps compatible contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SurfaceName = Literal["ios", "windows", "buddy-brain", "omni-buddy", "knowledge-vault"]
ParityStatus = Literal["contracted", "external-validation-required"]


@dataclass(frozen=True)
class SurfaceCapability:
    """A capability Buddy Agent must preserve for a related surface."""

    surface: SurfaceName
    capability_id: str
    owner_repo: str
    summary: str
    validation: str
    status: ParityStatus = "contracted"
    upstream_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SurfaceParity:
    """Parity contract for one external surface."""

    surface: SurfaceName
    owner_repo: str
    boundary: str
    capabilities: tuple[SurfaceCapability, ...]

    def capability_ids(self) -> tuple[str, ...]:
        """Return stable capability identifiers for this surface."""
        return tuple(capability.capability_id for capability in self.capabilities)

    def has_capability(self, capability_id: str) -> bool:
        """Return whether this surface declares the requested capability."""
        return capability_id in self.capability_ids()


REQUIRED_SURFACES: tuple[SurfaceName, ...] = (
    "ios",
    "windows",
    "buddy-brain",
    "omni-buddy",
    "knowledge-vault",
)

SURFACE_PARITY: tuple[SurfaceParity, ...] = (
    SurfaceParity(
        surface="ios",
        owner_repo="codysumpter-cloud/prismtek-apps",
        boundary="Phone-native Buddy UX and app-container runtime contracts.",
        capabilities=(
            SurfaceCapability(
                surface="ios",
                capability_id="buddy.identity",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary=(
                    "Identity, archetype, class, role, palette, "
                    "and voice selections."
                ),
                validation="Run BeMoreAgentShell BuddyContracts decoding tests.",
                upstream_refs=(
                    "apps/bemore-ios-native/BeMoreAgentShell/BuddyContracts.swift",
                ),
            ),
            SurfaceCapability(
                surface="ios",
                capability_id="buddy.progression",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary=(
                    "Level, XP, bond, evolution tier, anti-grind, "
                    "and proficiency state."
                ),
                validation="Run BeMoreAgentShell BuddyRuntimeTests.",
                upstream_refs=(
                    "apps/bemore-ios-native/BeMoreAgentShell/BuddyContracts.swift",
                ),
            ),
            SurfaceCapability(
                surface="ios",
                capability_id="buddy.appearance-profile",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary=(
                    "ASCII, pixel, customization, profile, "
                    "and render-state metadata."
                ),
                validation="Run BuddyAppearanceStudioTests and render checks.",
                upstream_refs=(
                    "apps/bemore-ios-native/BeMoreAgentShell/BuddyContracts.swift",
                    "apps/bemore-ios-native/BeMoreAgentShell/Features/Buddy/",
                ),
            ),
            SurfaceCapability(
                surface="ios",
                capability_id="buddy.runtime-events",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary="Idempotent runtime events with actor, payload, and receipts.",
                validation="Run BuddyRuntimeTests against event and state contracts.",
                upstream_refs=(
                    "apps/bemore-ios-native/BeMoreAgentShell/BuddyContracts.swift",
                ),
            ),
            SurfaceCapability(
                surface="ios",
                capability_id="buddy.trade-package",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary="Trade-ready Buddy snapshots with provenance metadata.",
                validation="Round-trip BuddyTradePackage JSON through app and agent.",
                upstream_refs=(
                    "apps/bemore-ios-native/BeMoreAgentShell/BuddyContracts.swift",
                ),
            ),
            SurfaceCapability(
                surface="ios",
                capability_id="llm.phone-native-runtime",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary="Phone inference uses LiteRT, MediaPipe, AI Edge, or MLC.",
                validation="Verify the app bundle contains a mobile runtime package.",
                status="external-validation-required",
                upstream_refs=("apps/bemore-macos/BEMORE_BUDDY_WINDOWS_GEMMA4.md",),
            ),
        ),
    ),
    SurfaceParity(
        surface="windows",
        owner_repo="codysumpter-cloud/prismtek-apps",
        boundary="Localhost desktop shell and Gemma gateway.",
        capabilities=(
            SurfaceCapability(
                surface="windows",
                capability_id="gemma4.desktop-gateway",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary="Gemma 4 routes through an OpenAI-compatible local endpoint.",
                validation="Run scripts/start-bemore-buddy-windows.ps1.",
                status="external-validation-required",
                upstream_refs=("apps/bemore-macos/BEMORE_BUDDY_WINDOWS_GEMMA4.md",),
            ),
            SurfaceCapability(
                surface="windows",
                capability_id="gemma4.status-endpoint",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary="Gateway exposes GET /api/gemma4/status.",
                validation="Invoke GET http://127.0.0.1:4320/api/gemma4/status.",
                status="external-validation-required",
                upstream_refs=("apps/bemore-macos/BEMORE_BUDDY_WINDOWS_GEMMA4.md",),
            ),
            SurfaceCapability(
                surface="windows",
                capability_id="gemma4.chat-endpoint",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary="Gateway exposes POST /api/gemma4/chat.",
                validation="Send the documented one-prompt smoke request.",
                status="external-validation-required",
                upstream_refs=("apps/bemore-macos/BEMORE_BUDDY_WINDOWS_GEMMA4.md",),
            ),
            SurfaceCapability(
                surface="windows",
                capability_id="gemma4.openapi-action",
                owner_repo="codysumpter-cloud/prismtek-apps",
                summary="Gateway exposes OpenAPI files for custom GPT Actions.",
                validation="Fetch /openapi.json and /api/openapi.json.",
                status="external-validation-required",
                upstream_refs=("apps/bemore-macos/BEMORE_BUDDY_WINDOWS_GEMMA4.md",),
            ),
        ),
    ),
    SurfaceParity(
        surface="buddy-brain",
        owner_repo="codysumpter-cloud/buddy-brain",
        boundary="Operator context, council policy, runbooks, and Codex bridge.",
        capabilities=(
            SurfaceCapability(
                surface="buddy-brain",
                capability_id="operator.startup-context",
                owner_repo="codysumpter-cloud/buddy-brain",
                summary="Startup context comes from core operator files.",
                validation="make doctor && make runtime-doctor",
                status="external-validation-required",
                upstream_refs=("README.md", "AGENTS.md", "context/RUNBOOK.md"),
            ),
            SurfaceCapability(
                surface="buddy-brain",
                capability_id="council.contracts",
                owner_repo="codysumpter-cloud/buddy-brain",
                summary="Council roles and operating policy stay in Buddy Brain.",
                validation="Validate context/council and config/council manifests.",
                status="external-validation-required",
                upstream_refs=("context/council/", "config/council/"),
            ),
            SurfaceCapability(
                surface="buddy-brain",
                capability_id="workspace.sync",
                owner_repo="codysumpter-cloud/buddy-brain",
                summary="Workspace sync and operator reports use adapter boundaries.",
                validation="make workspace-sync && make project-snapshot",
                status="external-validation-required",
                upstream_refs=("scripts/", "context/"),
            ),
            SurfaceCapability(
                surface="buddy-brain",
                capability_id="codex.bridge",
                owner_repo="codysumpter-cloud/buddy-brain",
                summary="Codex dispatch stays isolated through bridge artifacts.",
                validation="Validate mcp/codex-bridge with repo doctor checks.",
                status="external-validation-required",
                upstream_refs=("mcp/codex-bridge/",),
            ),
        ),
    ),
    SurfaceParity(
        surface="omni-buddy",
        owner_repo="codysumpter-cloud/omni-buddy",
        boundary="Offline-first voice, vision, transport, and local model behavior.",
        capabilities=(
            SurfaceCapability(
                surface="omni-buddy",
                capability_id="omni.local-routing",
                owner_repo="codysumpter-cloud/omni-buddy",
                summary="Local LLM routing supports Omni first with Ollama fallback.",
                validation="./scripts/bmo_omni_doctor.sh",
                status="external-validation-required",
                upstream_refs=("README.md", "config.json"),
            ),
            SurfaceCapability(
                surface="omni-buddy",
                capability_id="omni.voice-loop",
                owner_repo="codysumpter-cloud/omni-buddy",
                summary="Wake, listen, thinking, speaking, and error states.",
                validation="Run launch helper with wake/listen/speak smoke flow.",
                status="external-validation-required",
                upstream_refs=("README.md", "agent.py"),
            ),
            SurfaceCapability(
                surface="omni-buddy",
                capability_id="omni.vision-loop",
                owner_repo="codysumpter-cloud/omni-buddy",
                summary="Vision captioning can remain local or hybrid.",
                validation="Run validation matrix with local and hybrid vision modes.",
                status="external-validation-required",
                upstream_refs=("README.md", "docs/VALIDATION_MATRIX.md"),
            ),
            SurfaceCapability(
                surface="omni-buddy",
                capability_id="omni.transport-policy",
                owner_repo="codysumpter-cloud/omni-buddy",
                summary="Online, mesh, Reticulum fallback, and auto modes.",
                validation="./scripts/run_validation_matrix.sh",
                status="external-validation-required",
                upstream_refs=("README.md", "docs/COMMS_LAYER_PLAN.md"),
            ),
        ),
    ),
    SurfaceParity(
        surface="knowledge-vault",
        owner_repo="codysumpter-cloud/knowledge-vault",
        boundary="Obsidian-style source map, generated indexes, and provenance.",
        capabilities=(
            SurfaceCapability(
                surface="knowledge-vault",
                capability_id="vault.source-map",
                owner_repo="codysumpter-cloud/knowledge-vault",
                summary="Vault map defines inbox, projects, runbooks, and system areas.",
                validation="Verify 99-System/Vault Map.md before changing paths.",
                status="external-validation-required",
                upstream_refs=("99-System/Vault Map.md",),
            ),
            SurfaceCapability(
                surface="knowledge-vault",
                capability_id="vault.public-repo-steward",
                owner_repo="codysumpter-cloud/knowledge-vault",
                summary="Vault Steward tracks public repo metadata.",
                validation="Check generated markers and daily logs after refresh.",
                status="external-validation-required",
                upstream_refs=("99-System/Agents/Vault Steward/AGENT.md",),
            ),
            SurfaceCapability(
                surface="knowledge-vault",
                capability_id="vault.provenance",
                owner_repo="codysumpter-cloud/knowledge-vault",
                summary="Retrieved sources keep path, title, source id, and metadata.",
                validation="Run vault provider tests and inspect citation metadata.",
                upstream_refs=("99-System/", "infrastructure/"),
            ),
            SurfaceCapability(
                surface="knowledge-vault",
                capability_id="vault.private-boundary",
                owner_repo="codysumpter-cloud/knowledge-vault",
                summary="Automation must not read or write private credential notes.",
                validation="Confirm 00-Private/Credentials stays excluded from Git.",
                status="external-validation-required",
                upstream_refs=("99-System/Vault Map.md",),
            ),
        ),
    ),
)


def all_surface_parity() -> tuple[SurfaceParity, ...]:
    """Return all known surface parity contracts."""
    return SURFACE_PARITY


def get_surface_parity(surface: SurfaceName) -> SurfaceParity:
    """Return the parity contract for one surface."""
    for contract in SURFACE_PARITY:
        if contract.surface == surface:
            return contract
    raise KeyError(f"Unknown surface: {surface}")


def get_surface_capability(surface: SurfaceName, capability_id: str) -> SurfaceCapability:
    """Return a single capability from a surface contract."""
    contract = get_surface_parity(surface)
    for capability in contract.capabilities:
        if capability.capability_id == capability_id:
            return capability
    raise KeyError(f"Unknown capability for {surface}: {capability_id}")


def validate_required_surface_parity() -> tuple[str, ...]:
    """Return parity contract problems. Empty means the contract is complete."""
    problems: list[str] = []
    known_surfaces = {contract.surface for contract in SURFACE_PARITY}

    for surface in REQUIRED_SURFACES:
        if surface not in known_surfaces:
            problems.append(f"missing required surface: {surface}")

    for contract in SURFACE_PARITY:
        if not contract.capabilities:
            problems.append(f"{contract.surface} has no capabilities")
        seen_capabilities: set[str] = set()
        for capability in contract.capabilities:
            if capability.capability_id in seen_capabilities:
                problems.append(
                    f"{contract.surface} duplicate capability {capability.capability_id}"
                )
            seen_capabilities.add(capability.capability_id)
            if capability.surface != contract.surface:
                problems.append(
                    f"{capability.capability_id} is assigned to {capability.surface}, "
                    f"expected {contract.surface}"
                )
            if not capability.summary.strip():
                problems.append(f"{contract.surface}.{capability.capability_id} missing summary")
            if not capability.validation.strip():
                problems.append(
                    f"{contract.surface}.{capability.capability_id} missing validation"
                )
            if not capability.owner_repo.strip():
                problems.append(
                    f"{contract.surface}.{capability.capability_id} missing owner repo"
                )

    return tuple(problems)


def parity_summary_lines() -> tuple[str, ...]:
    """Return CLI-friendly parity summary lines."""
    lines: list[str] = []
    for contract in SURFACE_PARITY:
        lines.append(
            f"{contract.surface}: {len(contract.capabilities)} capabilities "
            f"owned by {contract.owner_repo}"
        )
    return tuple(lines)
