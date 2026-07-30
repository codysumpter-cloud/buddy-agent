from __future__ import annotations

import json
from pathlib import Path

import pytest

from buddy_agent.agent_life import AgentLifeError, AgentLifeService
from buddy_agent.tasks.models import TaskRecord, TaskStep


def _profile_path(tmp_path: Path) -> Path:
    path = tmp_path / "life-profile.json"
    path.write_text(
        json.dumps(
            {
                "schema": "prismtek-agent-life-profile-v1",
                "source_sha256": "task-profile",
                "agent": {"id": "task-buddy", "lineage": []},
                "constitution": {"immutable": True},
                "affect": {"drives": {}, "traits": {}},
                "reinforcement": {
                    "allowed_authorities": ["human", "host", "verifier"],
                    "max_preference_delta_per_event": 0.2,
                },
                "memory": {"require_provenance": True},
                "relationships": {"enabled": True},
                "development": {"initial_stage": "apprentice", "stages": []},
                "inheritance": {},
            }
        ),
        encoding="utf-8",
    )
    return path


def _service(tmp_path: Path) -> AgentLifeService:
    return AgentLifeService.from_paths(
        _profile_path(tmp_path),
        tmp_path / "state.json",
        tmp_path / "outbox",
    )


def test_verified_completed_task_teaches_workflow_preference(tmp_path: Path) -> None:
    task = TaskRecord(
        id="task-1234567890abcdef12345678",
        objective="Fix CI",
        risk="repo-mutation",
        status="completed",
        updated_at="2026-07-30T12:00:00+00:00",
        revision=8,
        plan=[TaskStep(id="step-1", title="Verify", status="completed")],
    )
    life = _service(tmp_path)
    result = life.apply_task_outcome(
        task,
        authority_kind="verifier",
        authority_id="github-actions",
        evidence=[{"type": "receipt", "ref": "run-123"}],
        subject_id="github-ci-recovery",
    )
    assert result["applied"] is True
    preference = life.runtime.explain_preference(
        {"type": "workflow", "id": "github-ci-recovery"}
    )
    assert preference["score"] > 0


def test_unfinished_or_unprovenanced_task_cannot_teach(tmp_path: Path) -> None:
    life = _service(tmp_path)
    running = TaskRecord(
        id="task-1234567890abcdef12345678",
        objective="Fix CI",
        risk="repo-mutation",
        status="running",
    )
    with pytest.raises(AgentLifeError, match="completed or failed"):
        life.apply_task_outcome(
            running,
            authority_kind="verifier",
            authority_id="ci",
            evidence=[{"type": "receipt", "ref": "run-123"}],
        )

    failed = TaskRecord(
        id="task-abcdef1234567890abcdef12",
        objective="Fix CI",
        risk="repo-mutation",
        status="failed",
    )
    with pytest.raises(AgentLifeError, match="at least one"):
        life.apply_task_outcome(
            failed,
            authority_kind="verifier",
            authority_id="ci",
            evidence=[],
        )
