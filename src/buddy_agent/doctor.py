"""Self-checks for the Buddy Agent scaffold."""

from __future__ import annotations

from dataclasses import dataclass

from .local_adapters import (
    LocalBuddyBrainAdapter,
    LocalKnowledgeVaultProvider,
    LocalOmniBuddyAdapter,
    LocalPrismtekAppBridge,
)
from .parity import validate_required_surface_parity
from .runtime import RuntimeEngine


@dataclass(frozen=True)
class DoctorCheck:
    """One doctor check result."""

    name: str
    ok: bool
    detail: str


def run_doctor() -> tuple[DoctorCheck, ...]:
    """Run scaffold health checks."""
    engine = RuntimeEngine(session_id="doctor")
    response = engine.receive("doctor")

    brain = LocalBuddyBrainAdapter(context={"status": "ready"})
    omni = LocalOmniBuddyAdapter()
    app = LocalPrismtekAppBridge()
    vault = LocalKnowledgeVaultProvider()
    parity_problems = validate_required_surface_parity()

    return (
        DoctorCheck(
            name="runtime",
            ok=response.startswith("Buddy Agent"),
            detail=f"messages={len(engine.state.messages)}",
        ),
        DoctorCheck(name="buddy-brain-adapter", ok=brain.health().ok, detail="local context"),
        DoctorCheck(name="omni-adapter", ok=omni.health().ok, detail=omni.route_text("ready")),
        DoctorCheck(name="app-bridge", ok=app.health().ok, detail="local events"),
        DoctorCheck(name="vault-provider", ok=vault.health().ok, detail="local index"),
        DoctorCheck(
            name="surface-parity",
            ok=not parity_problems,
            detail="complete" if not parity_problems else "; ".join(parity_problems),
        ),
    )


def doctor_ok(checks: tuple[DoctorCheck, ...]) -> bool:
    """Return whether all checks passed."""
    return all(check.ok for check in checks)
