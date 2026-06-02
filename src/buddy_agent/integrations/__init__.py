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
from .openmythos import (
    BuddyMythosConfig,
    get_variant_config,
    torch_backend_lines,
    torch_backend_status,
    training_plan_lines,
    variant_summary_lines,
)
from .runtime import BuddyIntegrationRuntime, IntegrationRunResult
from .symphony import (
    BuddyWorkflow,
    BuddyWorkIssue,
    BuddyWorkRunPlan,
    build_work_run_plan,
    create_local_workspace,
    load_workflow,
    parse_workflow_text,
)
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
    "BuddyMythosConfig",
    "BuddyWorkflow",
    "BuddyWorkIssue",
    "BuddyWorkRunPlan",
    "IntegrationCapability",
    "IntegrationId",
    "IntegrationRunResult",
    "IntegrationStatus",
    "IntegrationTarget",
    "build_work_run_plan",
    "create_local_workspace",
    "get_integration_target",
    "get_variant_config",
    "integration_summary_lines",
    "load_workflow",
    "parse_integration_id",
    "parse_workflow_text",
    "torch_backend_lines",
    "torch_backend_status",
    "training_plan_lines",
    "validate_integration_targets",
    "variant_summary_lines",
]
