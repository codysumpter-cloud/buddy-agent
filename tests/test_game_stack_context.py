from __future__ import annotations

import json
from pathlib import Path

import pytest

from buddy_agent import mcp_game
from buddy_agent.game_providers import ProviderStatus
from buddy_agent.game_stack_context import assemble_game_stack_context
from buddy_agent.mcp_server import BuddyMcpConfig


class CapturingProvider:
    def __init__(self) -> None:
        self.status = ProviderStatus(
            provider="test-provider",
            model="test-model",
            configured=True,
            local=True,
            network_required=False,
        )
        self.system = ""
        self.user = ""

    def complete(self, *, system: str, user: str) -> str:
        self.system = system
        self.user = user
        return '{"reply":"Stack ready","commands":[]}'


def fixture_stack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> BuddyMcpConfig:
    project = tmp_path / "project"
    vault = tmp_path / "vault"
    project.mkdir()
    vault.mkdir()
    (project / "AGENTS.md").write_text(
        "# BUAP policy\nNever claim success without evidence.\napi_key=super-secret-value\n",
        encoding="utf-8",
    )
    (project / "REVIEW.md").write_text(
        "# Review\nRepository writes require review.\n",
        encoding="utf-8",
    )
    (vault / "tiny-house.md").write_text(
        "Prismtek Buddies Tiny House uses durable tasks and verified room saves.",
        encoding="utf-8",
    )
    report = tmp_path / "buddy-brain-report.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "runs": 12,
                "verified_completion_rate": 0.75,
                "api_key": "must-redact",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("BUDDY_BRAIN_REPORT_PATH", str(report))
    monkeypatch.setenv("BUDDY_OMNI_ENDPOINT", "http://127.0.0.1:8799/api/omni")
    return BuddyMcpConfig(project_root=project, vault_root=vault)


def test_stack_context_collects_bounded_policy_memory_governance_and_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = fixture_stack(tmp_path, monkeypatch)
    context, receipt = assemble_game_stack_context(config, "Tiny House durable tasks")

    policy = context["buap_policy"]
    assert isinstance(policy, list)
    assert [item["name"] for item in policy] == ["AGENTS.md", "REVIEW.md"]
    serialized_policy = json.dumps(policy)
    assert "Never claim success without evidence" in serialized_policy
    assert "super-secret-value" not in serialized_policy
    assert "[REDACTED]" in serialized_policy

    evidence = context["knowledge_vault_evidence"]
    assert isinstance(evidence, list)
    assert len(evidence) == 1
    assert "durable tasks" in json.dumps(evidence)

    brain = context["buddy_brain_report"]
    assert isinstance(brain, dict)
    assert brain["verified_completion_rate"] == 0.75
    assert brain["api_key"] == "[redacted]"

    assert receipt.buap_policy_files == ("AGENTS.md", "REVIEW.md")
    assert set(receipt.buap_policy_hashes) == {"AGENTS.md", "REVIEW.md"}
    assert receipt.knowledge_vault_configured is True
    assert receipt.knowledge_vault_result_count == 1
    assert receipt.buddy_brain_report_loaded is True
    assert receipt.omni_buddy_transport_contract is True
    assert receipt.omni_buddy_endpoint_configured is True


def test_game_chat_passes_stack_context_to_provider_and_returns_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = fixture_stack(tmp_path, monkeypatch)
    provider = CapturingProvider()
    monkeypatch.setattr(mcp_game, "provider_from_env", lambda: provider)

    result = mcp_game._chat(
        config,
        {
            "message": "What should we do with the Tiny House task?",
            "context": {"mode": "play", "selected_asset_id": "desk-1"},
        },
    )

    assert result["reply"] == "Stack ready"
    assert result["stack"]["buap_policy_files"] == ["AGENTS.md", "REVIEW.md"]
    assert result["stack"]["knowledge_vault_result_count"] == 1
    assert result["claims"]["stack_context_is_bounded"] is True

    prompt = json.loads(provider.user)
    assert prompt["game_context"]["selected_asset_id"] == "desk-1"
    assert prompt["stack_context"]["buap_policy"]
    assert prompt["stack_context"]["knowledge_vault_evidence"]
    assert prompt["stack_context"]["buddy_brain_report"]["runs"] == 12
    assert "Treat BUAP policy as binding" in provider.system
