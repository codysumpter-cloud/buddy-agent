from buddy_agent.parity import (
    REQUIRED_SURFACES,
    all_surface_parity,
    get_surface_capability,
    get_surface_parity,
    parity_summary_lines,
    validate_required_surface_parity,
)


def test_required_surface_parity_is_complete():
    assert validate_required_surface_parity() == ()
    assert {contract.surface for contract in all_surface_parity()} == set(REQUIRED_SURFACES)


def test_ios_contract_covers_core_buddy_product_state():
    ios = get_surface_parity("ios")

    assert ios.owner_repo == "codysumpter-cloud/prismtek-apps"
    assert ios.has_capability("buddy.identity")
    assert ios.has_capability("buddy.progression")
    assert ios.has_capability("buddy.appearance-profile")
    assert ios.has_capability("buddy.runtime-events")
    assert ios.has_capability("buddy.trade-package")
    assert ios.has_capability("llm.phone-native-runtime")


def test_windows_contract_keeps_gateway_separate_from_phone_runtime():
    gateway = get_surface_capability("windows", "gemma4.desktop-gateway")

    assert gateway.status == "external-validation-required"
    assert "local endpoint" in gateway.summary
    assert "BEMORE_BUDDY_WINDOWS_GEMMA4.md" in gateway.upstream_refs[0]


def test_buddy_brain_and_omni_boundaries_are_explicit():
    brain = get_surface_parity("buddy-brain")
    omni = get_surface_parity("omni-buddy")

    assert brain.has_capability("operator.startup-context")
    assert brain.has_capability("council.contracts")
    assert brain.has_capability("codex.bridge")
    assert omni.has_capability("omni.local-routing")
    assert omni.has_capability("omni.voice-loop")
    assert omni.has_capability("omni.transport-policy")


def test_knowledge_vault_contract_preserves_private_boundary():
    vault = get_surface_parity("knowledge-vault")
    private_boundary = get_surface_capability("knowledge-vault", "vault.private-boundary")

    assert vault.has_capability("vault.source-map")
    assert vault.has_capability("vault.provenance")
    assert private_boundary.status == "external-validation-required"
    assert "private credential" in private_boundary.summary


def test_parity_summary_mentions_each_required_surface():
    summary = "\n".join(parity_summary_lines())

    for surface in REQUIRED_SURFACES:
        assert f"{surface}:" in summary
