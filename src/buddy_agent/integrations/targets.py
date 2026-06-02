"""Buddy-native integration targets for Hermes, Symphony, and OpenMythos."""

from __future__ import annotations

from .contracts import IntegrationCapability, IntegrationId, IntegrationTarget

REQUIRED_INTEGRATIONS: tuple[IntegrationId, ...] = (
    "hermes-agent",
    "symphony",
    "openmythos",
)

INTEGRATION_TARGETS: tuple[IntegrationTarget, ...] = (
    IntegrationTarget(
        integration_id="hermes-agent",
        buddy_name="Buddy Core Runtime",
        upstream_repo="NousResearch/hermes-agent",
        upstream_license="MIT",
        upstream_package="hermes-agent",
        summary=(
            "Self-improving agent runtime source for Buddy-native chat, model routing, "
            "tools, skills, memory, scheduling, terminal backends, and messaging surfaces."
        ),
        status="adapter-ready",
        capabilities=(
            IntegrationCapability(
                capability_id="terminal-chat",
                buddy_name="buddy runtime chat",
                upstream_name="hermes terminal CLI",
                summary="Interactive terminal chat loop and command surface.",
                status="mapped",
                source_path="hermes_cli/main.py, run_agent.py, cli.py",
                validation="Port command loop behind Buddy-native names and run Buddy CLI tests.",
            ),
            IntegrationCapability(
                capability_id="model-routing",
                buddy_name="Buddy model router",
                upstream_name="hermes model providers",
                summary="Provider/model switching with OpenAI-compatible endpoints.",
                status="adapter-ready",
                source_path="providers/, model_tools.py, hermes_cli/",
                runtime_command="buddy integrations run hermes-agent model-routing",
                requires_external_runtime=True,
                validation="Configure provider test doubles before network providers.",
            ),
            IntegrationCapability(
                capability_id="tools",
                buddy_name="Buddy tool registry",
                upstream_name="hermes tools and toolsets",
                summary="Runtime tool and toolset registry for agent actions.",
                status="mapped",
                source_path="tools/, toolsets.py, toolset_distributions.py",
                validation="Port safe tools first; gated tools require policy and tests.",
            ),
            IntegrationCapability(
                capability_id="skills",
                buddy_name="Buddy skill system",
                upstream_name="hermes skills system",
                summary="Procedural skills, skill discovery, and skill execution.",
                status="mapped",
                source_path="skills/, tools/skill_tools.py",
                validation="Preserve upstream attribution and agentskills notes.",
            ),
            IntegrationCapability(
                capability_id="memory",
                buddy_name="Buddy memory loop",
                upstream_name="hermes memory and recall",
                summary="Agent-curated memory, session search, and cross-session recall.",
                status="adapter-ready",
                source_path="agent/, tools/memory_tools.py, hermes_state.py",
                runtime_command="buddy integrations run hermes-agent memory",
                validation="Back memory provider with Buddy persistent memory before import parity.",
            ),
            IntegrationCapability(
                capability_id="scheduler",
                buddy_name="Buddy scheduled runs",
                upstream_name="hermes cron scheduler",
                summary="Scheduled natural-language tasks with platform delivery.",
                status="mapped",
                source_path="cron/",
                validation="Keep disabled until explicit schedule creation and cancellation tests exist.",
            ),
            IntegrationCapability(
                capability_id="messaging-gateway",
                buddy_name="Buddy app gateway",
                upstream_name="hermes messaging gateway",
                summary="Telegram, Discord, Slack, WhatsApp, Signal, and email concepts.",
                status="mapped",
                source_path="gateway/, tui_gateway/",
                validation="Each platform requires opt-in config, secret handling, and smoke tests.",
            ),
            IntegrationCapability(
                capability_id="subagents",
                buddy_name="Buddy delegated workstreams",
                upstream_name="hermes subagents and batch trajectories",
                summary="Isolated subagent workstreams and research trajectory helpers.",
                status="mapped",
                source_path="agent/, batch_runner.py, trajectory_compressor.py",
                validation="Port only after sandbox, workspace, and provenance policies are complete.",
            ),
        ),
    ),
    IntegrationTarget(
        integration_id="symphony",
        buddy_name="Buddy Work Orchestrator",
        upstream_repo="openai/symphony",
        upstream_license="Apache-2.0",
        upstream_package="symphony",
        summary=(
            "Engineering orchestration source for isolated implementation runs, work "
            "tracking, workspace creation, worker sessions, and proof-of-work reporting."
        ),
        status="native-runtime",
        capabilities=(
            IntegrationCapability(
                capability_id="workflow-contract",
                buddy_name="Buddy work runbook",
                upstream_name="Symphony WORKFLOW.md",
                summary="YAML-front-matter workflow contract plus task prompt body.",
                status="native-runtime",
                source_path="elixir/WORKFLOW.md, elixir/README.md",
                runtime_command="buddy integrations run symphony workflow-contract",
                validation="Buddy validates the contract shape without services.",
            ),
            IntegrationCapability(
                capability_id="tracker-local",
                buddy_name="Buddy local work tracker",
                upstream_name="Symphony tracker poller",
                summary="Load a local JSON work item and expose the next claimable issue.",
                status="native-runtime",
                source_path="src/buddy_agent/integrations/symphony.py",
                runtime_command="buddy integrations run symphony tracker-local [issues.json]",
                validation="Local tracker JSON is parsed without tokens or remote services.",
            ),
            IntegrationCapability(
                capability_id="workspace-spawn",
                buddy_name="Buddy workspace plan",
                upstream_name="Symphony workspace creation",
                summary="Plan an isolated workspace from a validated workflow and issue.",
                status="native-runtime",
                source_path="src/buddy_agent/integrations/symphony.py",
                runtime_command="buddy integrations run symphony workspace-spawn WORKFLOW.md",
                validation="Path policy is local; no hooks are executed.",
            ),
            IntegrationCapability(
                capability_id="work-runner",
                buddy_name="Buddy local work runner",
                upstream_name="Symphony worker run",
                summary="Create the local workspace prompt and JSON receipt for a work item.",
                status="native-runtime",
                source_path="src/buddy_agent/integrations/symphony.py",
                runtime_command="buddy integrations run symphony work-runner WORKFLOW.md",
                validation="Creates files only; no external services or worker process starts.",
            ),
            IntegrationCapability(
                capability_id="codex-app-server",
                buddy_name="Buddy agent worker bridge",
                upstream_name="Symphony Codex app-server session",
                summary="Expose the worker bridge contract for an explicit external worker.",
                status="adapter-ready",
                source_path="src/buddy_agent/integrations/symphony.py",
                runtime_command="buddy integrations run symphony codex-app-server",
                requires_external_runtime=True,
                validation="External worker launch remains explicit and outside default runtime.",
            ),
            IntegrationCapability(
                capability_id="observability",
                buddy_name="Buddy work receipts",
                upstream_name="Symphony dashboard/API",
                summary="Expose local JSON receipt and dashboard/API contract status.",
                status="native-runtime",
                source_path="src/buddy_agent/integrations/symphony.py",
                runtime_command="buddy integrations run symphony observability",
                validation="Local receipt surface is implemented; dashboard is not auto-started.",
            ),
        ),
    ),
    IntegrationTarget(
        integration_id="openmythos",
        buddy_name="Buddy Mythos Model Lab",
        upstream_repo="kyegomez/OpenMythos",
        upstream_license="MIT",
        upstream_package="open-mythos",
        summary=(
            "Recurrent-depth Transformer architecture source for Buddy model lab "
            "experiments, loop-depth metadata, and optional local PyTorch backends."
        ),
        status="native-runtime",
        capabilities=(
            IntegrationCapability(
                capability_id="architecture-contract",
                buddy_name="Buddy Mythos architecture contract",
                upstream_name="OpenMythos MythosConfig/OpenMythos",
                summary="Prelude, recurrent block, coda, attention choice, MoE, and loop depth contract.",
                status="native-runtime",
                source_path="src/buddy_agent/integrations/openmythos.py",
                runtime_command="buddy integrations run openmythos architecture-contract [variant]",
                validation="Buddy exposes dependency-light config validation in tests.",
            ),
            IntegrationCapability(
                capability_id="torch-model",
                buddy_name="Buddy Mythos PyTorch backend guard",
                upstream_name="OpenMythos torch model",
                summary="Optional backend availability check and import guard for PyTorch model work.",
                status="adapter-ready",
                source_path="src/buddy_agent/integrations/openmythos.py",
                runtime_command="buddy integrations run openmythos torch-model",
                requires_external_runtime=True,
                validation="Torch is optional; default install remains lightweight.",
            ),
            IntegrationCapability(
                capability_id="variant-configs",
                buddy_name="Buddy Mythos variants",
                upstream_name="OpenMythos model variants",
                summary="Named model scale configs for tiny, 1B, 3B, and 7B planning targets.",
                status="native-runtime",
                source_path="src/buddy_agent/integrations/openmythos.py",
                runtime_command="buddy integrations run openmythos variant-configs",
                validation="Variant factories are implemented without model construction.",
            ),
            IntegrationCapability(
                capability_id="training-script",
                buddy_name="Buddy Mythos training plan",
                upstream_name="OpenMythos training script",
                summary="Training plan metadata for explicit external training runs.",
                status="native-runtime",
                source_path="src/buddy_agent/integrations/openmythos.py",
                runtime_command="buddy integrations run openmythos training-script [variant]",
                validation="Training plans are emitted; training is not launched by default.",
            ),
        ),
    ),
)


def get_integration_target(integration_id: IntegrationId) -> IntegrationTarget:
    """Return one integration target by id."""
    for target in INTEGRATION_TARGETS:
        if target.integration_id == integration_id:
            return target
    raise KeyError(f"Unknown integration target: {integration_id}")


def validate_integration_targets() -> tuple[str, ...]:
    """Return registry problems. Empty means required targets are represented."""
    problems: list[str] = []
    known_ids = {target.integration_id for target in INTEGRATION_TARGETS}

    for required in REQUIRED_INTEGRATIONS:
        if required not in known_ids:
            problems.append(f"missing integration target: {required}")

    for target in INTEGRATION_TARGETS:
        if not target.capabilities:
            problems.append(f"{target.integration_id} has no capabilities")
        seen: set[str] = set()
        for capability in target.capabilities:
            if capability.capability_id in seen:
                problems.append(f"{target.integration_id} duplicate capability {capability.capability_id}")
            seen.add(capability.capability_id)
            if not capability.summary.strip():
                problems.append(f"{target.integration_id}.{capability.capability_id} missing summary")
            if capability.status == "native-runtime" and not capability.runtime_command:
                problems.append(
                    f"{target.integration_id}.{capability.capability_id} missing runtime command"
                )

    return tuple(problems)


def integration_summary_lines() -> tuple[str, ...]:
    """Return CLI-friendly summary lines for integration state."""
    lines: list[str] = []
    for target in INTEGRATION_TARGETS:
        native = len(target.native_capabilities())
        adapter = len(target.adapter_capabilities())
        mapped = len(target.mapped_capabilities())
        lines.append(
            f"{target.integration_id}: {native} native, {adapter} adapter-ready, "
            f"{mapped} mapped ({target.upstream_repo})"
        )
    return tuple(lines)
