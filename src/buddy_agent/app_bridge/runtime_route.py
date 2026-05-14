"""App bridge routes that talk to the Buddy runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AppChatRequest:
    """App-facing chat request."""

    prompt: str
    surface: str = "local"
    buddy_id: str = "default-buddy"


@dataclass(frozen=True)
class AppChatResponse:
    """App-facing chat response."""

    ok: bool
    message: str
    detail: str
    buddy_id: str
    surface: str


class RuntimeChatResult(Protocol):
    """Minimal shape returned by Buddy runtime chat routes."""

    ok: bool
    message: str
    detail: str


class CompanionShellLike(Protocol):
    """Minimal companion shell fields needed by app chat routes."""

    buddy_id: str


class AppChatRuntime(Protocol):
    """Minimal runtime capability needed by app chat routes."""

    companion_shell: CompanionShellLike

    def route_app_chat(self, prompt: str, *, surface: str = "local") -> RuntimeChatResult:
        """Run one app chat turn."""
        ...


def route_app_chat(runtime: AppChatRuntime, request: AppChatRequest) -> AppChatResponse:
    """Route an app chat request through the Buddy runtime."""
    result = runtime.route_app_chat(request.prompt, surface=request.surface)
    return AppChatResponse(
        ok=result.ok,
        message=result.message,
        detail=result.detail,
        buddy_id=runtime.companion_shell.buddy_id or request.buddy_id,
        surface=request.surface,
    )
