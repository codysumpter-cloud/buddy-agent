"""Model-runtime parity registry for Fable/Mythos-style Buddy work.

This module is deliberately contract-only. It does not import vendor SDKs, does not
ship model weights, and does not claim Claude Fable 5 / Mythos 5 equivalence.
It gives Buddy Agent a typed place to reason about what is covered by a local or
open architecture path versus what still requires a hosted model/runtime service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ParityStatus = Literal[
    "supported",
    "partial",
    "claimed-not-verified",
    "missing",
    "external-runtime-required",
]
SourceKind = Literal["anthropic-docs", "openmythos", "openfable", "desktop-client", "buddy"]


@dataclass(frozen=True)
class SourceReference:
    """A public source used to classify a model-runtime capability."""

    kind: SourceKind
    title: str
    url: str
    verified_on: str = "2026-06-15"


@dataclass(frozen=True)
class ModelRuntimeCapability:
    """One capability in the Fable/Mythos parity ledger."""

    capability_id: str
    label: str
    fable_mythos_status: ParityStatus
    openmythos_status: ParityStatus
    openfable_status: ParityStatus
    buddy_target_status: ParityStatus
    buddy_owner: str
    summary: str
    implementation_note: str
    validation: str
    sources: tuple[SourceReference, ...]


ANTHROPIC_FABLE_MYTHOS_DOC = SourceReference(
    kind="anthropic-docs",
    title="Introducing Claude Fable 5 and Claude Mythos 5",
    url=(
        "https://platform.claude.com/docs/en/about-claude/models/"
        "introducing-claude-fable-5-and-claude-mythos-5"
    ),
)

OPENMYTHOS_README = SourceReference(
    kind="openmythos",
    title="OpenMythos README",
    url="https://github.com/kyegomez/OpenMythos",
)

OPENFABLE_README = SourceReference(
    kind="openfable",
    title="OpenFable README",
    url="https://github.com/lovestaco/OpenFable",
)

CLAUDE_FABLE_DESKTOP_CLIENT = SourceReference(
    kind="desktop-client",
    title="anthropic-fable/claude-fable-5 desktop client",
    url="https://github.com/anthropic-fable/claude-fable-5",
)


MODEL_RUNTIME_PARITY: tuple[ModelRuntimeCapability, ...] = (
    ModelRuntimeCapability(
        capability_id="model.weights",
        label="Frontier trained model weights",
        fable_mythos_status="external-runtime-required",
        openmythos_status="missing",
        openfable_status="missing",
        buddy_target_status="external-runtime-required",
        buddy_owner="buddy-agent/providers",
        summary="Fable/Mythos are hosted proprietary models; open repos do not provide equivalent weights.",
        implementation_note=(
            "Buddy can route to hosted models or local open models, but must not claim OpenMythos "
            "or OpenFable is a trained Claude-class checkpoint."
        ),
        validation="Provider registry distinguishes hosted model IDs from local architecture experiments.",
        sources=(ANTHROPIC_FABLE_MYTHOS_DOC, OPENMYTHOS_README, OPENFABLE_README),
    ),
    ModelRuntimeCapability(
        capability_id="architecture.recurrent-depth",
        label="Recurrent-depth / looped transformer architecture",
        fable_mythos_status="claimed-not-verified",
        openmythos_status="partial",
        openfable_status="partial",
        buddy_target_status="partial",
        buddy_owner="buddy-agent/model-runtime",
        summary="OpenMythos/OpenFable implement a theoretical RDT-style architecture with loop depth.",
        implementation_note=(
            "Treat this as a research backend candidate, not an Anthropic-compatible runtime."
        ),
        validation="Import the package in an isolated optional mythos environment and run a tiny forward pass.",
        sources=(OPENMYTHOS_README, OPENFABLE_README),
    ),
    ModelRuntimeCapability(
        capability_id="context.1m-output.128k",
        label="1M context and 128k output",
        fable_mythos_status="supported",
        openmythos_status="claimed-not-verified",
        openfable_status="claimed-not-verified",
        buddy_target_status="missing",
        buddy_owner="buddy-agent/context-runtime",
        summary="Anthropic documents 1M context and 128k output; open repos only claim large configs.",
        implementation_note=(
            "Buddy needs explicit context-window accounting, stress tests, and truncation/compaction before "
            "large-context claims are allowed."
        ),
        validation="Run synthetic long-context smoke tests and record token accounting receipts.",
        sources=(ANTHROPIC_FABLE_MYTHOS_DOC, OPENMYTHOS_README, OPENFABLE_README),
    ),
    ModelRuntimeCapability(
        capability_id="thinking.adaptive-effort",
        label="Adaptive thinking and effort control",
        fable_mythos_status="supported",
        openmythos_status="partial",
        openfable_status="partial",
        buddy_target_status="partial",
        buddy_owner="buddy-agent/runtime-policy",
        summary="Claude exposes effort/runtime controls; OpenMythos exposes loop depth/ACT-like mechanics.",
        implementation_note=(
            "Map Buddy effort levels to model loop budgets, hosted effort parameters, or tool-budget policy "
            "without exposing raw chain of thought."
        ),
        validation="Unit-test effort presets against max loops, task budget, and receipt output.",
        sources=(ANTHROPIC_FABLE_MYTHOS_DOC, OPENMYTHOS_README),
    ),
    ModelRuntimeCapability(
        capability_id="tools.code-memory-compaction-vision",
        label="Tools, code execution, memory, compaction, and vision",
        fable_mythos_status="supported",
        openmythos_status="missing",
        openfable_status="missing",
        buddy_target_status="partial",
        buddy_owner="buddy-agent/skills-and-integrations",
        summary="These are runtime/product capabilities, not just neural architecture capabilities.",
        implementation_note=(
            "Buddy should implement these as guarded adapters: memory store, code sandbox, tool protocol, "
            "context manager, and multimodal routing."
        ),
        validation="Run skill policy validation, sandbox smoke tests, memory round trips, and vision adapter smoke tests.",
        sources=(ANTHROPIC_FABLE_MYTHOS_DOC,),
    ),
    ModelRuntimeCapability(
        capability_id="safety.refusal-fallback-billing",
        label="Fable refusal/fallback/billing behavior",
        fable_mythos_status="supported",
        openmythos_status="missing",
        openfable_status="missing",
        buddy_target_status="partial",
        buddy_owner="buddy-agent/safety-policy",
        summary="Fable has refusal classifiers and fallback/billing semantics; Mythos omits the classifiers.",
        implementation_note=(
            "Buddy needs provider-normalized refusal objects and explicit fallback receipts. Billing claims stay "
            "vendor-specific and must be sourced from provider responses."
        ),
        validation="Simulate refusal, fallback, and no-output cases with sanitized receipts.",
        sources=(ANTHROPIC_FABLE_MYTHOS_DOC,),
    ),
)


def all_model_runtime_capabilities() -> tuple[ModelRuntimeCapability, ...]:
    """Return the Fable/Mythos parity ledger."""

    return MODEL_RUNTIME_PARITY


def missing_buddy_capabilities() -> tuple[ModelRuntimeCapability, ...]:
    """Return capabilities Buddy has not implemented as a safe local/runtime feature yet."""

    return tuple(
        capability
        for capability in MODEL_RUNTIME_PARITY
        if capability.buddy_target_status in {"missing", "external-runtime-required"}
    )


def parity_summary_lines() -> tuple[str, ...]:
    """Return CLI-friendly model-runtime parity summary lines."""

    return tuple(
        f"{capability.capability_id}: Buddy={capability.buddy_target_status}; "
        f"OpenMythos={capability.openmythos_status}; OpenFable={capability.openfable_status}"
        for capability in MODEL_RUNTIME_PARITY
    )
