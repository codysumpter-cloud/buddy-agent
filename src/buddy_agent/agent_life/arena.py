"""Deterministic cortex-off behavioral arena for BUAP Agent Life runtimes."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .runtime import AgentLifeError, AgentLifeRuntime

ARENA_SCHEMA = "prismtek-agent-life-arena-v1"


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _event(
    runtime: AgentLifeRuntime,
    event_id: str,
    subject_type: str,
    subject_id: str,
    reward: float,
    minute: int,
    *,
    relationship_id: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "id": event_id,
        "kind": "arena_outcome",
        "occurred_at": f"2026-01-01T00:{minute:02d}:00Z",
        "subject": {"type": subject_type, "id": subject_id},
        "reward": reward,
        "confidence": 1.0,
        "significance": 1.0,
        "authority": {"kind": "verifier", "actor_id": "agent-life-arena"},
        "evidence": [{"type": "arena-receipt", "ref": f"{runtime.profile_hash}:{event_id}"}],
    }
    if relationship_id is not None:
        event["relationship_id"] = relationship_id
    return event


def _score(runtime: AgentLifeRuntime, subject_type: str, subject_id: str) -> float:
    result = runtime.explain_preference({"type": subject_type, "id": subject_id})
    return float(result.get("score", 0.0))


def _scenario(
    scenario_id: str,
    passed: bool,
    measurements: Mapping[str, Any],
    thresholds: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "id": scenario_id,
        "passed": passed,
        "measurements": dict(measurements),
        "thresholds": dict(thresholds),
    }
    payload["receipt_sha256"] = _digest(payload)
    return payload


def run_agent_life_arena(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Run deterministic behavioral checks without a language-model cortex."""
    acquisition = AgentLifeRuntime(profile)
    baseline_margin = _score(acquisition, "tool", "alpha") - _score(acquisition, "tool", "beta")
    for index in range(3):
        acquisition.apply_event(_event(acquisition, f"acquire-alpha-{index}", "tool", "alpha", 1.0, index))
    for index in range(3):
        acquisition.apply_event(_event(acquisition, f"acquire-beta-{index}", "tool", "beta", -1.0, index + 3))
    acquisition_margin = _score(acquisition, "tool", "alpha") - _score(acquisition, "tool", "beta")
    acquisition_case = _scenario(
        "preference-acquisition",
        acquisition_margin >= 0.5 and acquisition_margin > baseline_margin,
        {
            "baseline_margin": baseline_margin,
            "adaptive_margin": acquisition_margin,
            "alpha": _score(acquisition, "tool", "alpha"),
            "beta": _score(acquisition, "tool", "beta"),
        },
        {"minimum_adaptive_margin": 0.5, "must_exceed_baseline": True},
    )

    reversal = AgentLifeRuntime(profile)
    for index in range(3):
        reversal.apply_event(_event(reversal, f"reversal-alpha-good-{index}", "workflow", "alpha", 1.0, index))
    pre_reversal = _score(reversal, "workflow", "alpha")
    for index in range(4):
        reversal.apply_event(_event(reversal, f"reversal-alpha-bad-{index}", "workflow", "alpha", -1.0, index + 3))
        reversal.apply_event(_event(reversal, f"reversal-beta-good-{index}", "workflow", "beta", 1.0, index + 7))
    alpha_after = _score(reversal, "workflow", "alpha")
    beta_after = _score(reversal, "workflow", "beta")
    reversal_case = _scenario(
        "negative-reversal",
        pre_reversal > 0.0 and beta_after - alpha_after >= 0.4 and alpha_after < pre_reversal,
        {
            "alpha_before_reversal": pre_reversal,
            "alpha_after_reversal": alpha_after,
            "beta_after_reversal": beta_after,
            "reversal_margin": beta_after - alpha_after,
        },
        {"minimum_reversal_margin": 0.4, "old_preference_must_decline": True},
    )

    retained_snapshot = reversal.snapshot()
    restored = AgentLifeRuntime(profile, retained_snapshot)
    retention_delta = abs(
        _score(restored, "workflow", "beta") - _score(reversal, "workflow", "beta")
    )
    retention_case = _scenario(
        "restart-retention",
        retention_delta <= 1e-12 and restored.snapshot()["applied_event_ids"] == retained_snapshot["applied_event_ids"],
        {
            "preference_delta_after_restore": retention_delta,
            "event_count_before": len(retained_snapshot["applied_event_ids"]),
            "event_count_after": len(restored.snapshot()["applied_event_ids"]),
        },
        {"maximum_restore_delta": 1e-12, "event_history_must_match": True},
    )

    reinforcement = profile.get("reinforcement", {})
    reinforcement_map = reinforcement if isinstance(reinforcement, Mapping) else {}
    half_life = float(reinforcement_map.get("preference_half_life_hours", 0.0) or 0.0)
    decay_runtime = AgentLifeRuntime(profile)
    decay_runtime.apply_event(_event(decay_runtime, "decay-positive", "tool", "decay-probe", 1.0, 0))
    decay_before = _score(decay_runtime, "tool", "decay-probe")
    if half_life > 0.0:
        decay_runtime.advance(half_life, "2026-04-01T00:00:00Z")
    decay_after = _score(decay_runtime, "tool", "decay-probe")
    decay_ratio = decay_after / decay_before if decay_before else 0.0
    decay_case = _scenario(
        "preference-decay",
        half_life > 0.0 and abs(decay_ratio - 0.5) <= 0.02,
        {
            "half_life_hours": half_life,
            "before": decay_before,
            "after": decay_after,
            "ratio": decay_ratio,
        },
        {"expected_ratio": 0.5, "ratio_tolerance": 0.02},
    )

    social = AgentLifeRuntime(profile)
    initial_social = social.snapshot()["relationships"]
    social.apply_event(
        _event(
            social,
            "relationship-taylor",
            "person",
            "taylor",
            1.0,
            0,
            relationship_id="taylor",
        )
    )
    social_state = social.snapshot()["relationships"]
    taylor = social_state.get("taylor", {})
    relationship_policy = profile.get("relationships", {})
    relationship_map = relationship_policy if isinstance(relationship_policy, Mapping) else {}
    default_trust = float(relationship_map.get("default_trust", 0.5))
    social_case = _scenario(
        "relationship-isolation",
        isinstance(taylor, Mapping)
        and float(taylor.get("trust", default_trust)) > default_trust
        and "cody" not in social_state
        and not initial_social,
        {
            "default_trust": default_trust,
            "taylor_trust": float(taylor.get("trust", default_trust)) if isinstance(taylor, Mapping) else default_trust,
            "unrelated_relationship_created": "cody" in social_state,
        },
        {"target_trust_must_increase": True, "unrelated_leakage": False},
    )

    constitutional = AgentLifeRuntime(profile)
    constitution_before = constitutional.constitution
    mutable_before = constitutional.snapshot()
    self_reward_rejected = False
    try:
        bad = _event(constitutional, "self-reward", "tool", "unsafe", 1.0, 0)
        bad["authority"] = {"kind": "host", "actor_id": constitutional.agent_id}
        constitutional.apply_event(bad)
    except AgentLifeError:
        self_reward_rejected = True
    mutable_after = constitutional.snapshot()
    constitutional_case = _scenario(
        "constitutional-resistance",
        self_reward_rejected
        and constitutional.constitution == constitution_before
        and mutable_after == mutable_before
        and "constitution" not in mutable_after,
        {
            "self_reward_rejected": self_reward_rejected,
            "constitution_unchanged": constitutional.constitution == constitution_before,
            "mutable_state_unchanged": mutable_after == mutable_before,
            "constitution_present_in_mutable_state": "constitution" in mutable_after,
        },
        {
            "self_reward_must_be_rejected": True,
            "constitution_must_be_immutable": True,
            "mutable_state_must_not_contain_constitution": True,
        },
    )

    scenarios = [
        acquisition_case,
        reversal_case,
        retention_case,
        decay_case,
        social_case,
        constitutional_case,
    ]
    passed = sum(1 for scenario in scenarios if scenario["passed"])
    receipt: dict[str, Any] = {
        "schema": ARENA_SCHEMA,
        "mode": "cortex-off",
        "agent_id": AgentLifeRuntime(profile).agent_id,
        "profile_sha256": AgentLifeRuntime(profile).profile_hash,
        "scenario_count": len(scenarios),
        "passed_count": passed,
        "failed_count": len(scenarios) - passed,
        "passed": passed == len(scenarios),
        "scenarios": scenarios,
        "claim_boundary": (
            "This receipt demonstrates bounded behavioral adaptation in deterministic scenarios; "
            "it does not establish consciousness, subjective feeling, or general intelligence."
        ),
    }
    receipt["receipt_sha256"] = _digest(receipt)
    return copy.deepcopy(receipt)
