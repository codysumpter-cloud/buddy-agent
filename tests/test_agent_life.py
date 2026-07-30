from __future__ import annotations

import json
from pathlib import Path

import pytest

from buddy_agent.agent_life import AgentLifeError, AgentLifeService
from buddy_agent.agent_life.store import HOST_SCHEMA


def _profile() -> dict[str, object]:
    return {
        "schema": "prismtek-agent-life-profile-v1",
        "source_sha256": "profile-test",
        "agent": {"id": "buddy-test", "lineage": []},
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
                    "half_life_hours": 10,
                },
                "completion": {
                    "initial": 0.4,
                    "baseline": 0.4,
                    "min": 0,
                    "max": 1,
                    "half_life_hours": 10,
                },
            },
            "traits": {
                "patience": {
                    "initial": 0.5,
                    "baseline": 0.5,
                    "min": 0.2,
                    "max": 0.9,
                    "plasticity": 1,
                }
            },
        },
        "reinforcement": {
            "allowed_authorities": ["human", "host", "verifier"],
            "max_drive_delta_per_event": 0.2,
            "max_trait_delta_per_event": 0.02,
            "max_preference_delta_per_event": 0.2,
            "preference_half_life_hours": 100,
            "event_effects": {
                "task_succeeded": {
                    "drives": {"completion": -0.1},
                    "traits": {"patience": 0.1},
                }
            },
        },
        "memory": {
            "require_provenance": True,
            "max_evidence_items": 4,
            "max_dedup_event_ids": 100,
        },
        "relationships": {
            "enabled": True,
            "default_trust": 0.5,
            "max_delta_per_event": 0.05,
        },
        "development": {
            "initial_stage": "apprentice",
            "stages": [
                {"id": "apprentice", "minimum_experience": 0},
                {"id": "specialist", "minimum_experience": 1.5},
            ],
        },
        "inheritance": {},
    }


def _event(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": "evt-1",
        "kind": "task_succeeded",
        "occurred_at": "2026-07-30T12:00:00Z",
        "subject": {"type": "tool", "id": "github"},
        "reward": 0.8,
        "confidence": 1.0,
        "significance": 1.0,
        "authority": {"kind": "verifier", "actor_id": "ci"},
        "evidence": [{"type": "receipt", "ref": "run-123"}],
        "effects": {"drives": {"curiosity": 0.1}},
    }
    value.update(overrides)
    return value


def _service(tmp_path: Path) -> AgentLifeService:
    profile_path = tmp_path / "life-profile.json"
    profile_path.write_text(json.dumps(_profile()), encoding="utf-8")
    return AgentLifeService.from_paths(
        profile_path,
        tmp_path / "state.json",
        tmp_path / "outbox",
    )


def test_valid_outcome_persists_state_and_outbox(tmp_path: Path) -> None:
    life = _service(tmp_path)
    result = life.apply_outcome(_event())
    assert result["applied"] is True
    assert Path(str(result["outbox_path"])).is_file()
    persisted = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert persisted["schema"] == HOST_SCHEMA
    assert persisted["pending_memory_events"] == {}
    assert persisted["state"]["preferences"]["tool:github"]["score"] > 0
    assert "constitution" not in persisted["state"]


def test_negative_outcome_reverses_preference(tmp_path: Path) -> None:
    life = _service(tmp_path)
    life.apply_outcome(_event())
    positive = life.runtime.explain_preference({"type": "tool", "id": "github"})["score"]
    life.apply_outcome(_event(id="evt-2", kind="task_failed", reward=-1.0))
    assert life.runtime.explain_preference({"type": "tool", "id": "github"})["score"] < positive


def test_reload_retains_state_and_duplicate_is_idempotent(tmp_path: Path) -> None:
    life = _service(tmp_path)
    life.apply_outcome(_event())
    reloaded = _service(tmp_path)
    before = reloaded.runtime.snapshot()
    duplicate = reloaded.apply_outcome(_event())
    assert duplicate["duplicate"] is True
    assert reloaded.runtime.snapshot() == before
    assert len(list((tmp_path / "outbox").glob("*.json"))) == 1


def test_pending_publication_recovers_on_restart(tmp_path: Path) -> None:
    life = _service(tmp_path)
    result = life.runtime.apply_event(_event())
    memory = result["memory_event"]
    assert isinstance(memory, dict)
    life.store.save(life.runtime.snapshot(), {"evt-1": memory})
    assert not list((tmp_path / "outbox").glob("*.json"))
    recovered = _service(tmp_path)
    assert recovered.pending == {}
    assert len(list((tmp_path / "outbox").glob("*.json"))) == 1
    persisted = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert persisted["pending_memory_events"] == {}


def test_self_reinforcement_and_missing_evidence_are_rejected(tmp_path: Path) -> None:
    life = _service(tmp_path)
    with pytest.raises(AgentLifeError, match="may not reinforce itself"):
        life.apply_outcome(_event(authority={"kind": "host", "actor_id": "buddy-test"}))
    with pytest.raises(AgentLifeError, match="requires provenance"):
        life.apply_outcome(_event(evidence=[]))


def test_relationships_are_person_scoped(tmp_path: Path) -> None:
    life = _service(tmp_path)
    life.apply_outcome(
        _event(subject={"type": "person", "id": "taylor"}, relationship_id="taylor")
    )
    relationships = life.runtime.snapshot()["relationships"]
    assert relationships["taylor"]["trust"] > 0.5
    assert "cody" not in relationships


def test_profile_hash_mismatch_is_refused(tmp_path: Path) -> None:
    life = _service(tmp_path)
    life.apply_outcome(_event())
    modified = _profile()
    modified["source_sha256"] = "different"
    (tmp_path / "life-profile.json").write_text(json.dumps(modified), encoding="utf-8")
    with pytest.raises(AgentLifeError, match="different life profile"):
        AgentLifeService.from_paths(
            tmp_path / "life-profile.json",
            tmp_path / "state.json",
            tmp_path / "outbox",
        )


def test_decay_and_status_are_persisted(tmp_path: Path) -> None:
    life = _service(tmp_path)
    life.apply_outcome(_event())
    before = life.runtime.explain_preference({"type": "tool", "id": "github"})["score"]
    life.advance(100, "2026-08-03T16:00:00Z")
    after = life.runtime.explain_preference({"type": "tool", "id": "github"})["score"]
    assert 0 < after < before
    status = life.status()
    assert status["pending_memory_events"] == 0
    assert "not proof of consciousness" in status["claim_boundary"]
