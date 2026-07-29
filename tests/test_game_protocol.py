from __future__ import annotations

import json

import pytest

from buddy_agent.game_protocol import (
    GameProtocolError,
    normalize_context,
    normalize_message,
    normalize_model_response,
)
from buddy_agent.game_providers import DisabledProvider, OpenAIResponsesProvider, provider_from_env


def test_game_context_redacts_secret_keys_and_limits_commands() -> None:
    context = normalize_context(
        {
            "mode": "play",
            "access_token": "do-not-store",
            "nearby_items": [{"asset_id": "desk-1"}],
        }
    )
    assert context["access_token"] == "[redacted]"

    response = normalize_model_response(
        json.dumps(
            {
                "reply": "On it.",
                "commands": [
                    {"name": "buddy.use_item", "arguments": {"asset_id": "desk-1"}},
                    {"name": "shell.exec", "arguments": {"command": "rm -rf /"}},
                ],
            }
        )
    )
    assert response == {
        "reply": "On it.",
        "commands": [{"name": "buddy.use_item", "arguments": {"asset_id": "desk-1"}}],
    }


def test_plain_text_provider_output_remains_a_safe_reply() -> None:
    assert normalize_model_response("Hey buddy!") == {"reply": "Hey buddy!", "commands": []}


def test_message_contract_rejects_empty_and_oversized_input() -> None:
    with pytest.raises(GameProtocolError, match="required"):
        normalize_message("   ")
    with pytest.raises(GameProtocolError, match="exceeds"):
        normalize_message("x" * 4001)


def test_provider_selection_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUDDY_PROVIDER", "disabled")
    provider = provider_from_env()
    assert isinstance(provider, DisabledProvider)
    assert provider.status.configured is False


def test_openai_responses_adapter_extracts_output_text(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": '{"reply":"Ready","commands":[]}'},
                    ]
                }
            ]
        }

    monkeypatch.setattr("buddy_agent.game_providers._post_json", fake_post)
    provider = OpenAIResponsesProvider("test-key", model="test-model")
    assert provider.complete(system="system", user="user") == '{"reply":"Ready","commands":[]}'
