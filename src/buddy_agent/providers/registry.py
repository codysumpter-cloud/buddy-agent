"""Provider registry and safe environment selection."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping

from .base import BaseProvider
from .local import LocalEchoProvider

ProviderFactory = Callable[[], BaseProvider]

_PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "local": LocalEchoProvider,
}


def _env_bool(environ: Mapping[str, str], name: str, *, default: bool) -> bool:
    value = environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def provider_names() -> tuple[str, ...]:
    """Return supported provider names."""
    return tuple(sorted(_PROVIDER_FACTORIES))


def create_provider(name: str | None = None, *, network_enabled: bool = False) -> BaseProvider:
    """Create a provider with conservative fallback to local."""
    requested = (name or "local").strip().lower() or "local"
    if requested != "local" and not network_enabled:
        return LocalEchoProvider()
    factory = _PROVIDER_FACTORIES.get(requested)
    if factory is None:
        return LocalEchoProvider()
    return factory()


def create_provider_from_env(environ: Mapping[str, str] | None = None) -> BaseProvider:
    """Create the configured provider from environment variables."""
    env = environ if environ is not None else os.environ
    return create_provider(
        env.get("BUDDY_PROVIDER", "local"),
        network_enabled=_env_bool(env, "BUDDY_NETWORK_ENABLED", default=False),
    )
