"""Buddy Agent package."""

from .config import BuddyAgentConfig
from .entrypoint import BuddyRuntimeEntrypoint
from .local_adapters import (
    LocalBuddyBrainAdapter,
    LocalKnowledgeVaultProvider,
    LocalOmniBuddyAdapter,
    LocalPrismtekAppBridge,
)
from .metadata import PROJECT_NAME, VERSION
from .parity import SurfaceCapability, SurfaceParity, all_surface_parity

__all__ = [
    "BuddyAgentConfig",
    "BuddyRuntimeEntrypoint",
    "LocalBuddyBrainAdapter",
    "LocalKnowledgeVaultProvider",
    "LocalOmniBuddyAdapter",
    "LocalPrismtekAppBridge",
    "PROJECT_NAME",
    "SurfaceCapability",
    "SurfaceParity",
    "VERSION",
    "all_surface_parity",
]
