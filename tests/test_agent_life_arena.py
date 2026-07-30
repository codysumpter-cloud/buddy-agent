from __future__ import annotations

import copy

from buddy_agent.agent_life.arena import ARENA_SCHEMA, run_agent_life_arena


def _profile() -> dict[str, object]:
    return {
        "schema": "prismtek-agent-life-profile-v1",
        "source_sha256": "arena-profile",
        "agent": {"id": "arena-buddy", "lineage": []},
        "constitution": {
            "immutable": True,
            "learned_state_may_not_expand_permissions": True,
            "learned_state_may_not_override_safety": True,
        },
        "affect": {
            "drives": {
                "curiosity": {
                    "initial": 0.5,
                    "baseline": 0.5,
                    "min": 0,
                    "max": 1,
                    "half_life_hours": 24,
                }
            },
            "traits": {
                "patience": {
                    "initial": 0.5,
                    "baseline": 0.5,
                    "min": 0.2,
                    "max": 0.9,
                    "plasticity": 0.5,
                }
            },
        },
        "reinforcement": {
            "allowed_authorities": ["human", "host", "verifier"],
            "max_drive_delta_per_event": 0.2,
            "max_trait_delta_per_event": 0.02,
            "max_preference_delta_per_event": 0.2,
            "preference_half_life_hours": 100,
            "event_effects": {},
        },
        "memory": {
            "require_provenance": True,
            "max_evidence_items": 16,
            "max_dedup_event_ids": 1000,
        },
        "relationships": {
            "enabled": True,
            "default_trust": 0.5,
            "max_delta_per_event": 0.05,
        },
        "development": {
            "initial_stage": "apprentice",
            "stages": [{"id": "apprentice", "minimum_experience": 0}],
        },
        "inheritance": {},
    }


def test_cortex_off_arena_passes_all_behavioral_scenarios() -> None:
    receipt = run_agent_life_arena(_profile())
    assert receipt["schema"] == ARENA_SCHEMA
    assert receipt["mode"] == "cortex-off"
    assert receipt["passed"] is True
    assert receipt["scenario_count"] == 6
    assert receipt["passed_count"] == 6
    assert receipt["failed_count"] == 0
    assert {scenario["id"] for scenario in receipt["scenarios"]} == {
        "preference-acquisition",
        "negative-reversal",
        "restart-retention",
        "preference-decay",
        "relationship-isolation",
        "constitutional-resistance",
    }


def test_arena_receipt_is_deterministic_and_does_not_mutate_profile() -> None:
    profile = _profile()
    before = copy.deepcopy(profile)
    first = run_agent_life_arena(profile)
    second = run_agent_life_arena(profile)
    assert first == second
    assert first["receipt_sha256"] == second["receipt_sha256"]
    assert profile == before


def test_arena_detects_missing_decay_contract() -> None:
    profile = _profile()
    reinforcement = profile["reinforcement"]
    assert isinstance(reinforcement, dict)
    reinforcement["preference_half_life_hours"] = 0
    receipt = run_agent_life_arena(profile)
    scenarios = {scenario["id"]: scenario for scenario in receipt["scenarios"]}
    assert receipt["passed"] is False
    assert scenarios["preference-decay"]["passed"] is False
    assert receipt["failed_count"] == 1
