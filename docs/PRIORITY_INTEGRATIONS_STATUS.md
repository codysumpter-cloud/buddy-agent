# Priority Integrations Status

This document tracks the first three requested upstream integrations: Hermes Agent, Symphony, and OpenMythos.

Status vocabulary:

- `native-runtime`: Buddy contains local runnable code and tests for the capability.
- `adapter-ready`: Buddy exposes a safe runtime seam, but external runtime validation or deeper source porting is still required.
- `mapped`: Buddy knows the source capability and landing zone, but the implementation is not runnable inside Buddy yet.

The machine-readable source of truth is `src/buddy_agent/integrations/`.

## Current status

| Upstream | Buddy name | License | Buddy status | Notes |
| --- | --- | --- | --- | --- |
| `NousResearch/hermes-agent` | Buddy Core Runtime | MIT | `adapter-ready` | Major runtime source identified. Full feature parity is not complete. |
| `codysumpter-cloud/symphony` | Buddy Work Orchestrator | Apache-2.0 | `adapter-ready` | Workflow contract is locally runnable; Linear/Codex orchestration remains external. |
| `codysumpter-cloud/OpenMythos` | Buddy Mythos Model Lab | MIT | `adapter-ready` | Architecture contract is locally runnable; PyTorch backend remains optional. |

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

Source: `codysumpter-cloud/symphony`.

Important upstream capabilities identified from the source README and Elixir README:

- `WORKFLOW.md` contract with YAML front matter and Markdown body
- work tracker polling
- isolated workspace creation
- Codex app-server worker sessions
- optional observability dashboard/API
- live/e2e validation against external services

Buddy-native state:

- `workflow-contract`: `native-runtime`
- `codex-app-server`: `adapter-ready`
- `tracker-linear`: `mapped`
- `workspace-spawn`: `mapped`
- `observability`: `mapped`

The current Buddy runtime can validate a minimal Symphony workflow contract without launching external services.

## OpenMythos

Source: `codysumpter-cloud/OpenMythos`.

Important upstream capabilities identified from the source README and `open_mythos/main.py`:

- `MythosConfig`
- `OpenMythos`
- Prelude / recurrent block / coda architecture
- GQA and MLA attention choices
- MoE feed-forward layer with shared experts
- recurrent loop depth controls
- LTI-stable input injection
- optional PyTorch generation backend
- variant configs and training scripts

Buddy-native state:

- `architecture-contract`: `native-runtime`
- `torch-model`: `adapter-ready`
- `variant-configs`: `mapped`
- `training-script`: `mapped`

The current Buddy runtime exposes a dependency-light architecture contract and intentionally does not add PyTorch to the default install.

## Runtime commands

```bash
buddy integrations
buddy integrations describe hermes-agent
buddy integrations describe symphony
buddy integrations describe openmythos
buddy integrations run openmythos architecture-contract
buddy integrations run symphony workflow-contract
buddy integrations run symphony workflow-contract /path/to/WORKFLOW.md
```

## Next porting steps

1. Port Hermes Agent configuration and model-provider selection behind Buddy-native names.
2. Port Hermes tool registry and safe tools into Buddy runtime tests.
3. Port Hermes skills system with provenance and upstream attribution.
4. Expand Symphony workflow parsing into a typed Buddy work orchestration contract.
5. Add optional OpenMythos extras and a backend import guard for PyTorch model construction.
6. Add third-party notices before copying substantial upstream source files.
