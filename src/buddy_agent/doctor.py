"""Self-checks for the Buddy Agent Alpha Runtime Plus."""

from __future__ import annotations

from dataclasses import dataclass

from .companion import load_companion_shell
from .local_adapters import (
    LocalBuddyBrainAdapter,
    LocalKnowledgeVaultProvider,
    LocalOmniBuddyAdapter,
    LocalPrismtekAppBridge,
)
from .memory import PersistentNoteIndex
from .parity import validate_required_surface_parity
from .runtime import RuntimeEngine


@dataclass(frozen=True)
class DoctorCheck:
    """One doctor check result."""

    name: str
    ok: bool
    detail: str


def run_doctor() -> tuple[DoctorCheck, ...]:
    """Run local runtime health checks."""
    engine = RuntimeEngine(session_id="doctor")
    response = engine.receive("doctor")

    memory = PersistentNoteIndex()
    brain = LocalBuddyBrainAdapter(context={"status": "ready"})
    omni = LocalOmniBuddyAdapter()
    app = LocalPrismtekAppBridge()
    vault = LocalKnowledgeVaultProvider(index=memory)
    shell = load_companion_shell()
    parity_problems = validate_required_surface_parity()

    return (
        DoctorCheck(
            name="runtime",
            ok=response.startswith("Buddy runtime"),
            detail=f"messages={len(engine.state.messages)} backend={engine.config.backend}",
        ),
        DoctorCheck(
            name="runtime-config",
            ok=engine.config.backend != "",
            detail=engine.config.name,
        ),
        DoctorCheck(name="buddy-brain-adapter", ok=brain.health().ok, detail="local context"),
        DoctorCheck(name="omni-adapter", ok=omni.health().ok, detail=omni.route_text("ready")),
        DoctorCheck(name="app-bridge", ok=app.health().ok, detail="local events"),
        DoctorCheck(name="vault-provider", ok=vault.health().ok, detail="persistent note index"),
        DoctorCheck(name="companion-shell", ok=shell.buddy_id != "", detail=shell.display_name),
        DoctorCheck(
            name="surface-parity",
            ok=not parity_problems,
            detail="complete" if not parity_problems else "; ".join(parity_problems),
        ),
    )


def doctor_ok(checks: tuple[DoctorCheck, ...]) -> bool:
    """Return whether all checks passed."""
    return all(check.ok for check in checks)
