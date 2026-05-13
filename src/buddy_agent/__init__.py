"""Buddy Agent package."""

from .config import BuddyAgentConfig
from .local_adapters import (
    LocalBuddyBrainAdapter,
    LocalKnowledgeVaultProvider,
    LocalOmniBuddyAdapter,
    LocalPrismtekAppBridge,
)
from .metadata import PROJECT_NAME, VERSION

__all__ = [
    "BuddyAgentConfig",
    "LocalBuddyBrainAdapter",
    "LocalKnowledgeVaultProvider",
    "LocalOmniBuddyAdapter",
    "LocalPrismtekAppBridge",
    "PROJECT_NAME",
    "VERSION",
]
