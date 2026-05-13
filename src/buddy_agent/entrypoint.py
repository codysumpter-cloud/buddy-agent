"""Runtime execution entrypoint for configured Buddy Agent runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .alpha import AlphaRuntimeResult, BuddyAlphaRuntime
from .config import BuddyAgentConfig


@dataclass
class BuddyRuntimeEntrypoint:
    """Small execution facade for config-loaded runtime commands."""

    runtime: BuddyAlphaRuntime

    @classmethod
    def from_env(cls) -> BuddyRuntimeEntrypoint:
        """Create an entrypoint from environment config."""
        return cls(runtime=BuddyAlphaRuntime.from_config(BuddyAgentConfig.from_env()))

    @classmethod
    def from_config_file(cls, path: str | Path) -> BuddyRuntimeEntrypoint:
        """Create an entrypoint from a JSON config file."""
        return cls(runtime=BuddyAlphaRuntime.from_config(BuddyAgentConfig.from_file(path)))

    def execute(self, command: str, text: str) -> AlphaRuntimeResult:
        """Execute one supported runtime command."""
        if command == "chat":
            return self.runtime.chat(text)
        if command == "remember":
            return self.runtime.remember(text)
        if command == "recall":
            return self.runtime.recall(text)
        if command == "alpha":
            smoke_results = self.runtime.smoke()
            ok = all(result.ok for result in smoke_results)
            return AlphaRuntimeResult(
                ok=ok,
                message="\n".join(result.message for result in smoke_results),
            )
        return AlphaRuntimeResult(ok=False, message=f"Unknown runtime command: {command}")
