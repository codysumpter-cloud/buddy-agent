# Priority Integrations Status

This document tracks the requested upstream integrations: Hermes Agent, Symphony, and OpenMythos.

Status vocabulary:

- `native-runtime`: Buddy contains local runnable code and tests for the capability.
- `adapter-ready`: Buddy exposes a safe runtime seam, but external validation or heavier dependencies are still required.
- `mapped`: Buddy knows the source capability and landing zone, but the implementation is not runnable inside Buddy yet.

The machine-readable source of truth is `src/buddy_agent/integrations/`.

## Current status

| Upstream | Buddy name | License | Buddy status | Notes |
| --- | --- | --- | --- | --- |
| `NousResearch/hermes-agent` | Buddy Core Runtime | MIT | `adapter-ready` | Major runtime source identified. Full feature parity is not complete. |
| `openai/symphony` | Buddy Work Orchestrator | Apache-2.0 | `native-runtime` | Local workflow parsing, tracker JSON, workspace planning, file creation, and receipt output are implemented. |
| `kyegomez/OpenMythos` | Buddy Mythos Model Lab | MIT | `native-runtime` | Dependency-light architecture configs, variants, backend guard, and training plans are implemented. |

## Hermes Agent

Source: `NousResearch/hermes-agent`.

Important upstream capabilities identified from the source README and package metadata:

- terminal chat runtime
- model provider and model selection
- tool registry and toolsets
- skills system
- memory and recall loop
- cron scheduler
- messaging gateway
- subagents, batch trajectories, and trajectory compression
- terminal backends and sandbox surfaces

Buddy-native state:

- `model-routing`: `adapter-ready`
- `memory`: `adapter-ready`
- `terminal-chat`: `mapped`
- `tools`: `mapped`
- `skills`: `mapped`
- `scheduler`: `mapped`
- `messaging-gateway`: `mapped`
- `subagents`: `mapped`

Do not claim Hermes Agent full parity until those modules are ported, rebranded, wired into Buddy commands/runtime surfaces, and tested in this repository.

## Symphony

Source: `openai/symphony`.

Buddy-native implemented state:

- `workflow-contract`: `native-runtime`
- `tracker-local`: `native-runtime`
- `workspace-spawn`: `native-runtime`
- `work-runner`: `native-runtime`
- `observability`: `native-runtime`
- `codex-app-server`: `adapter-ready`

What Buddy now does locally:

- parses Symphony-style `WORKFLOW.md` front matter and Markdown prompt body;
- validates required `tracker`, `workspace`, `hooks`, `agent`, and `codex` sections;
- reads a local JSON tracker issue;
- renders `{{ issue.identifier }}`, `{{ issue.title }}`, `{{ issue.body }}`, and `{{ issue.priority }}` placeholders;
- plans an isolated workspace path;
- creates `BUDDY_WORK_PROMPT.md` and `buddy_work_run.json` receipts;
- reports worker bridge and observability status without launching external services.

The current Buddy runtime intentionally does not auto-start Codex app-server, hooks, dashboards, or remote tracker calls.

## OpenMythos

Source: `kyegomez/OpenMythos`.

Buddy-native implemented state:

- `architecture-contract`: `native-runtime`
- `variant-configs`: `native-runtime`
- `training-script`: `native-runtime`
- `torch-model`: `adapter-ready`

What Buddy now does locally:

- exposes `BuddyMythosConfig` with Prelude / recurrent block / coda architecture metadata;
- validates recurrent-depth, attention, MoE, key-value head, and stability constraints;
- exposes tiny, 1B, 3B, and 7B planning variants;
- reports optional Torch backend availability without importing Torch;
- provides a plan-only training surface so heavy training is never launched by default.

The optional backend install path is:

```bash
pip install -e .[mythos]
```

## Runtime commands

```bash
buddy integrations
buddy integrations describe hermes-agent
buddy integrations describe symphony
buddy integrations describe openmythos

buddy integrations run openmythos architecture-contract
buddy integrations run openmythos architecture-contract buddy-mythos-3b
buddy integrations run openmythos variant-configs
buddy integrations run openmythos torch-model
buddy integrations run openmythos training-script buddy-mythos-1b

buddy integrations run symphony workflow-contract
buddy integrations run symphony workflow-contract /path/to/WORKFLOW.md
buddy integrations run symphony tracker-local /path/to/issues.json
buddy integrations run symphony workspace-spawn /path/to/WORKFLOW.md
buddy integrations run symphony work-runner /path/to/WORKFLOW.md
buddy integrations run symphony observability
buddy integrations run symphony codex-app-server
```

## Test commands

```bash
python -m pytest tests/test_integrations.py
python -m ruff check src tests
python -m mypy src/buddy_agent
```

## Remaining real parity gaps

1. Port Hermes Agent configuration/model-provider selection into Buddy-native runtime code.
2. Port Hermes safe tool registry and safe tool execution tests.
3. Port Hermes skill discovery/execution with provenance and policy checks.
4. Add remote tracker adapters only behind explicit secrets/config gates.
5. Add Codex app-server launching only behind explicit operator approval and process supervision.
6. Add real OpenMythos Torch construction tests under optional `[mythos]` CI.
7. Add third-party notices before copying substantial upstream source files.
