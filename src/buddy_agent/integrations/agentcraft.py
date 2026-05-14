"""Optional local AgentCraft HUD integration.

AgentCraft is observability only. Buddy Agent remains the runtime source of truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

AgentCraftEventType = Literal[
    "hero_active",
    "mission_start",
    "file_access",
    "bash_command",
    "hero_idle",
]

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]

DEFAULT_EVENT_URL = "http://localhost:2468/event"
DEFAULT_CLIENT = "buddy-agent"
DEFAULT_COMMAND_LIMIT = 120
DEFAULT_TIMEOUT_SECONDS = 0.75
SECRET_KEY_RE = re.compile(r"token|secret|password|authorization|cookie|credential|key", re.I)
BEARER_RE = re.compile(r"Bearer\s+\S+", re.I)
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
ALLOWED_EVENT_TYPES: tuple[AgentCraftEventType, ...] = (
    "hero_active",
    "mission_start",
    "file_access",
    "bash_command",
    "hero_idle",
)


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def stable_session_id(cwd: str | Path | None = None) -> str:
    source = str(Path(cwd or Path.cwd()).resolve())
    digest = hashlib.md5(source.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
    return f"buddy_{digest}"


def is_local_http_endpoint(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and parsed.hostname in LOCAL_HOSTS


def redact_value(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        redacted: dict[str, JsonValue] = {}
        for key, nested in value.items():
            redacted[key] = "[redacted]" if SECRET_KEY_RE.search(key) else redact_value(nested)
        return redacted
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return BEARER_RE.sub("Bearer [redacted]", value)
    return value


@dataclass(frozen=True)
class AgentCraftConfig:
    enabled: bool = False
    event_url: str = DEFAULT_EVENT_URL
    client: str = DEFAULT_CLIENT
    redact_prompts: bool = True
    max_command_chars: int = DEFAULT_COMMAND_LIMIT
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> AgentCraftConfig:
        max_command_raw = os.environ.get("BUDDY_AGENTCRAFT_MAX_COMMAND_CHARS")
        timeout_raw = os.environ.get("BUDDY_AGENTCRAFT_TIMEOUT_SECONDS")
        return cls(
            enabled=env_flag("BUDDY_AGENTCRAFT_ENABLED", default=False),
            event_url=os.environ.get("BUDDY_AGENTCRAFT_EVENT_URL", DEFAULT_EVENT_URL),
            client=os.environ.get("BUDDY_AGENTCRAFT_CLIENT", DEFAULT_CLIENT),
            redact_prompts=env_flag("BUDDY_AGENTCRAFT_REDACT_PROMPTS", default=True),
            max_command_chars=int(max_command_raw or DEFAULT_COMMAND_LIMIT),
            timeout_seconds=float(timeout_raw or DEFAULT_TIMEOUT_SECONDS),
        )

    def doctor_lines(self) -> tuple[str, ...]:
        endpoint_status = "ok" if is_local_http_endpoint(self.event_url) else "fail"
        enabled_status = "enabled" if self.enabled else "disabled"
        return (
            f"ok agentcraft-mode: {enabled_status}",
            f"{endpoint_status} agentcraft-endpoint: {self.event_url}",
            f"ok agentcraft-client: {self.client}",
            f"ok agentcraft-redaction: prompts={'on' if self.redact_prompts else 'off'}",
        )


@dataclass(frozen=True)
class AgentCraftEvent:
    type: AgentCraftEventType
    payload: dict[str, JsonValue] = field(default_factory=dict)
    cwd: str = field(default_factory=lambda: str(Path.cwd()))
    session_id: str = field(default_factory=stable_session_id)

    def as_payload(self, config: AgentCraftConfig) -> dict[str, JsonValue]:
        event_payload = redact_value(self.payload)
        if not isinstance(event_payload, dict):
            event_payload = {}
        normalized: dict[str, JsonValue] = {
            "client": config.client,
            "sessionId": self.session_id,
            "cwd": self.cwd,
            "type": self.type,
            **event_payload,
        }
        if config.redact_prompts and isinstance(normalized.get("prompt"), str):
            normalized["prompt"] = "[redacted]"
        command = normalized.get("command")
        if isinstance(command, str) and config.max_command_chars > 0:
            normalized["command"] = command[: config.max_command_chars]
        return normalized


@dataclass(frozen=True)
class AgentCraftEmitResult:
    ok: bool
    skipped: bool
    reason: str
    status: int | None = None
    event: dict[str, JsonValue] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "ok": self.ok,
                "skipped": self.skipped,
                "reason": self.reason,
                "status": self.status,
                "event": self.event,
            },
            sort_keys=True,
        )


class AgentCraftBridge:
    def __init__(self, config: AgentCraftConfig | None = None) -> None:
        self.config = config or AgentCraftConfig.from_env()

    def emit(self, event: AgentCraftEvent) -> AgentCraftEmitResult:
        payload = event.as_payload(self.config)
        if event.type not in ALLOWED_EVENT_TYPES:
            return AgentCraftEmitResult(
                False,
                True,
                f"Unsupported AgentCraft event type: {event.type}",
                event=payload,
            )
        if not self.config.enabled:
            return AgentCraftEmitResult(
                True,
                True,
                "BUDDY_AGENTCRAFT_ENABLED is not set",
                event=payload,
            )
        if not is_local_http_endpoint(self.config.event_url):
            return AgentCraftEmitResult(
                False,
                True,
                "AgentCraft endpoint must be local HTTP(S).",
                event=payload,
            )
        try:
            request = Request(
                self.config.event_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"content-type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                status = response.status
            return AgentCraftEmitResult(
                200 <= status < 300,
                False,
                "posted",
                status=status,
                event=payload,
            )
        except (OSError, URLError, TimeoutError) as error:
            return AgentCraftEmitResult(False, True, str(error), event=payload)


def parse_event_type(value: str) -> AgentCraftEventType:
    if value not in ALLOWED_EVENT_TYPES:
        supported = ", ".join(ALLOWED_EVENT_TYPES)
        raise ValueError(f"Unsupported AgentCraft event type: {value}. Supported: {supported}")
    return cast(AgentCraftEventType, value)


def parse_payload_json(raw: str | None) -> dict[str, JsonValue]:
    if raw is None or raw.strip() == "":
        return {}
    value: Any = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("AgentCraft payload must be a JSON object")
    return cast(dict[str, JsonValue], value)
