"""Optional Buddy Agent integrations."""

from .agentcraft import (
    AgentCraftBridge,
    AgentCraftConfig,
    AgentCraftEmitResult,
    AgentCraftEvent,
)
from .contracts import (
    IntegrationCapability,
    IntegrationId,
    IntegrationStatus,
    IntegrationTarget,
    parse_integration_id,
)
from .runtime import BuddyIntegrationRuntime, IntegrationRunResult
from .targets import (
    get_integration_target,
    integration_summary_lines,
    validate_integration_targets,
)

__all__ = [
    "AgentCraftBridge",
    "AgentCraftConfig",
    "AgentCraftEmitResult",
    "AgentCraftEvent",
    "BuddyIntegrationRuntime",
    "IntegrationCapability",
    "IntegrationId",
    "IntegrationRunResult",
    "IntegrationStatus",
    "IntegrationTarget",
    "get_integration_target",
    "integration_summary_lines",
    "parse_integration_id",
    "validate_integration_targets",
]
