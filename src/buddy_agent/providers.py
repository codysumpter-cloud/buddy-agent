"""Capability-reporting model providers for the local Buddy runtime."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Protocol, cast

DEFAULT_OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
DEFAULT_OLLAMA_MODEL = "qwen3:8b"
MAX_RESPONSE_BYTES = 1_000_000


class ProviderError(RuntimeError):
    """A provider failed without exposing credentials or raw response bodies."""


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    model: str
    configured: bool
    local: bool
    network_required: bool
    structured_game_protocol: bool = True

    def to_dict(self) -> dict[str, object]:
        return cast(dict[str, object], asdict(self))


class ModelProvider(Protocol):
    @property
    def status(self) -> ProviderStatus: ...

    def complete(self, *, system: str, user: str) -> str: ...


def _post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"content-type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise ProviderError(f"provider returned HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderError("provider request failed") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ProviderError("provider response exceeded the size limit")
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProviderError("provider returned invalid JSON") from error
    if not isinstance(decoded, dict):
        raise ProviderError("provider returned a non-object response")
    return cast(dict[str, Any], decoded)


def _openai_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    output = payload.get("output", [])
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        if parts:
            return "\n".join(parts)
    raise ProviderError("OpenAI response contained no output text")


class DisabledProvider:
    @property
    def status(self) -> ProviderStatus:
        return ProviderStatus(
            provider="disabled",
            model="none",
            configured=False,
            local=True,
            network_required=False,
        )

    def complete(self, *, system: str, user: str) -> str:
        del system, user
        raise ProviderError("no Buddy model provider is configured")


class OpenAIResponsesProvider:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_OPENAI_MODEL,
        endpoint: str = DEFAULT_OPENAI_RESPONSES_URL,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint

    @property
    def status(self) -> ProviderStatus:
        return ProviderStatus(
            provider="openai-responses",
            model=self.model,
            configured=bool(self.api_key),
            local=False,
            network_required=True,
        )

    def complete(self, *, system: str, user: str) -> str:
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is not configured")
        payload = _post_json(
            self.endpoint,
            {
                "model": self.model,
                "instructions": system,
                "input": user,
            },
            headers={"authorization": f"Bearer {self.api_key}"},
        )
        return _openai_output_text(payload)


class OllamaProvider:
    def __init__(
        self,
        *,
        model: str = DEFAULT_OLLAMA_MODEL,
        endpoint: str = DEFAULT_OLLAMA_CHAT_URL,
    ) -> None:
        self.model = model
        self.endpoint = endpoint

    @property
    def status(self) -> ProviderStatus:
        return ProviderStatus(
            provider="ollama-chat",
            model=self.model,
            configured=True,
            local=True,
            network_required=False,
        )

    def complete(self, *, system: str, user: str) -> str:
        payload = _post_json(
            self.endpoint,
            {
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        message = payload.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        raise ProviderError("Ollama response contained no message content")


def provider_from_env() -> ModelProvider:
    selected = os.getenv("BUDDY_PROVIDER", "").strip().lower()
    if not selected:
        selected = "openai" if os.getenv("OPENAI_API_KEY", "").strip() else "ollama"
    if selected in {"off", "none", "disabled"}:
        return DisabledProvider()
    if selected in {"openai", "openai-responses", "responses"}:
        return OpenAIResponsesProvider(
            os.getenv("OPENAI_API_KEY", "").strip(),
            model=os.getenv("BUDDY_MODEL", DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL,
            endpoint=os.getenv("OPENAI_RESPONSES_URL", DEFAULT_OPENAI_RESPONSES_URL).strip()
            or DEFAULT_OPENAI_RESPONSES_URL,
        )
    if selected in {"ollama", "ollama-chat", "local"}:
        return OllamaProvider(
            model=os.getenv("BUDDY_MODEL", DEFAULT_OLLAMA_MODEL).strip() or DEFAULT_OLLAMA_MODEL,
            endpoint=os.getenv("OLLAMA_CHAT_URL", DEFAULT_OLLAMA_CHAT_URL).strip()
            or DEFAULT_OLLAMA_CHAT_URL,
        )
    raise ProviderError(f"unsupported Buddy provider: {selected}")
