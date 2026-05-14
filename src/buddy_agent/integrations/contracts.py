"""Typed contracts for Buddy-native integrations.

These contracts deliberately separate three states:

- mapped: Buddy knows the upstream feature and where it should land.
- adapter-ready: Buddy exposes a safe runtime seam, but external validation is still required.
- native-runtime: Buddy has a local runnable implementation covered by Buddy tests.

Do not mark a capability as native-runtime until it is wired into Buddy code and tested here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

IntegrationId = Literal["hermes-agent", "symphony", "openmythos"]
IntegrationStatus = Literal["mapped", "adapter-ready", "native-runtime"]


@dataclass(frozen=True)
class IntegrationCapability:
    """One upstream capability and its Buddy-native integration status."""

    capability_id: str
    buddy_name: str
    upstream_name: str
    summary: str
    status: IntegrationStatus
    source_path: str
    runtime_command: str = ""
    requires_external_runtime: bool = False
    validation: str = ""


@dataclass(frozen=True)
class IntegrationTarget:
    """An upstream project targeted for Buddy-native integration."""

    integration_id: IntegrationId
    buddy_name: str
    upstream_repo: str
    upstream_license: str
    upstream_package: str
    summary: str
    status: IntegrationStatus
    capabilities: tuple[IntegrationCapability, ...]

    def capability_ids(self) -> tuple[str, ...]:
        """Return stable capability identifiers for this integration target."""
        return tuple(capability.capability_id for capability in self.capabilities)

    def native_capabilities(self) -> tuple[IntegrationCapability, ...]:
        """Return capabilities currently implemented as Buddy-native runtime code."""
        return tuple(
            capability
            for capability in self.capabilities
            if capability.status == "native-runtime"
        )

    def adapter_capabilities(self) -> tuple[IntegrationCapability, ...]:
        """Return capabilities with a Buddy runtime seam but external runtime needs."""
        return tuple(
            capability
            for capability in self.capabilities
            if capability.status == "adapter-ready"
        )

    def mapped_capabilities(self) -> tuple[IntegrationCapability, ...]:
        """Return capabilities that are mapped but not runnable in Buddy yet."""
        return tuple(
            capability for capability in self.capabilities if capability.status == "mapped"
        )

    def get_capability(self, capability_id: str) -> IntegrationCapability:
        """Return one capability by id."""
        for capability in self.capabilities:
            if capability.capability_id == capability_id:
                return capability
        raise KeyError(f"Unknown capability for {self.integration_id}: {capability_id}")
