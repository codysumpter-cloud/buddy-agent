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
            "Self-improving agent runtime source for Buddy-native chat, "
            "model routing, tools, skills, memory, scheduling, terminal "
            "backends, and messaging surfaces."
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
                validation=(
                    "Port command loop behind Buddy-native names and run "
                    "Buddy CLI tests."
                ),
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
                validation=(
                    "Back memory provider with Buddy persistent memory before "
                    "import parity."
                ),
            ),
            IntegrationCapability(
                capability_id="scheduler",
                buddy_name="Buddy scheduled runs",
                upstream_name="hermes cron scheduler",
                summary="Scheduled natural-language tasks with platform delivery.",
                status="mapped",
                source_path="cron/",
                validation=(
                    "Keep disabled until explicit schedule creation and "
                    "cancellation tests exist."
                ),
            ),
            IntegrationCapability(
                capability_id="messaging-gateway",
                buddy_name="Buddy app gateway",
                upstream_name="hermes messaging gateway",
                summary="Telegram, Discord, Slack, WhatsApp, Signal, and email concepts.",
                status="mapped",
                source_path="gateway/, tui_gateway/",
                validation=(
                    "Each platform requires opt-in config, secret handling, "
                    "and smoke tests."
                ),
            ),
            IntegrationCapability(
                capability_id="subagents",
                buddy_name="Buddy delegated workstreams",
                upstream_name="hermes subagents and batch trajectories",
                summary="Isolated subagent workstreams and research trajectory helpers.",
                status="mapped",
                source_path="agent/, batch_runner.py, trajectory_compressor.py",
                validation=(
                    "Port only after sandbox, workspace, and provenance "
                    "policies are complete."
                ),
            ),
        ),
    ),
    IntegrationTarget(
        integration_id="symphony",
        buddy_name="Buddy Work Orchestrator",
        upstream_repo="codysumpter-cloud/symphony",
        upstream_license="Apache-2.0",
        upstream_package="symphony-elixir",
        summary=(
            "Engineering orchestration source for isolated implementation runs, "
            "work tracking, workspace creation, Codex app-server sessions, and "
            "proof-of-work reporting."
        ),
        status="adapter-ready",
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
                capability_id="tracker-linear",
                buddy_name="Buddy work tracker adapter",
                upstream_name="Symphony Linear poller",
                summary="Poll a tracker for candidate work and claim active issues.",
                status="mapped",
                source_path="elixir/lib/, elixir/README.md",
                validation=(
                    "Requires opt-in tracker token handling and disposable "
                    "integration tests."
                ),
            ),
            IntegrationCapability(
                capability_id="workspace-spawn",
                buddy_name="Buddy workspace spawn",
                upstream_name="Symphony workspace creation",
                summary="Create isolated workspaces and run bootstrap hooks.",
                status="mapped",
                source_path="elixir/lib/, elixir/WORKFLOW.md",
                validation=(
                    "Needs path policy, repo allowlist, and cleanup tests before "
                    "default use."
                ),
            ),
            IntegrationCapability(
                capability_id="codex-app-server",
                buddy_name="Buddy agent worker bridge",
                upstream_name="Symphony Codex app-server session",
                summary="Launch and supervise Codex app-server sessions for work.",
                status="adapter-ready",
                source_path="elixir/lib/, elixir/README.md",
                runtime_command="buddy integrations run symphony codex-app-server",
                requires_external_runtime=True,
                validation="External Codex app-server and tracker validation required.",
            ),
            IntegrationCapability(
                capability_id="observability",
                buddy_name="Buddy work dashboard bridge",
                upstream_name="Symphony Phoenix dashboard/API",
                summary="Expose run state through dashboard and JSON API concepts.",
                status="mapped",
                source_path="elixir/lib/, elixir/README.md",
                validation="Port API contracts before adding Phoenix runtime deps.",
            ),
        ),
    ),
    IntegrationTarget(
        integration_id="openmythos",
        buddy_name="Buddy Mythos Model Lab",
        upstream_repo="codysumpter-cloud/OpenMythos",
        upstream_license="MIT",
        upstream_package="open-mythos",
        summary=(
            "Recurrent-depth Transformer model architecture source for Buddy "
            "model lab experiments, loop-depth metadata, and optional local "
            "PyTorch backends."
        ),
        status="adapter-ready",
        capabilities=(
            IntegrationCapability(
                capability_id="architecture-contract",
                buddy_name="Buddy Mythos architecture contract",
                upstream_name="OpenMythos MythosConfig/OpenMythos",
                summary=(
                    "Prelude, recurrent block, coda, attention choice, MoE, "
                    "and loop depth contract."
                ),
                status="native-runtime",
                source_path="open_mythos/main.py",
                runtime_command="buddy integrations run openmythos architecture-contract",
                validation="Buddy exposes a dependency-light contract in tests.",
            ),
            IntegrationCapability(
                capability_id="torch-model",
                buddy_name="Buddy Mythos PyTorch backend",
                upstream_name="OpenMythos torch model",
                summary="PyTorch model with generate and recurrent loop controls.",
                status="adapter-ready",
                source_path="open_mythos/main.py",
                runtime_command="buddy integrations run openmythos torch-model",
                requires_external_runtime=True,
                validation=(
                    "Do not add Torch to default install; load only behind "
                    "optional backend."
                ),
            ),
            IntegrationCapability(
                capability_id="variant-configs",
                buddy_name="Buddy Mythos variants",
                upstream_name="OpenMythos model variants",
                summary="Named model scale configs from 1B through 1T targets.",
                status="mapped",
                source_path="open_mythos/__init__.py, open_mythos/main.py",
                validation="Port config factories before model construction commands.",
            ),
            IntegrationCapability(
                capability_id="training-script",
                buddy_name="Buddy Mythos training adapter",
                upstream_name="OpenMythos training script",
                summary="FineWeb-Edu training script and distributed training notes.",
                status="mapped",
                source_path="training/3b_fine_web_edu.py",
                validation=(
                    "Training remains external until resource, dataset, and "
                    "checkpoint policies exist."
                ),
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
                problems.append(
                    f"{target.integration_id} duplicate capability "
                    f"{capability.capability_id}"
                )
            seen.add(capability.capability_id)
            if not capability.summary.strip():
                problems.append(
                    f"{target.integration_id}.{capability.capability_id} missing summary"
                )
            if capability.status == "native-runtime" and not capability.runtime_command:
                problems.append(
                    f"{target.integration_id}.{capability.capability_id} "
                    "missing runtime command"
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
