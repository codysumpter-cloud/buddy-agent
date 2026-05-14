# Buddy Training and AgentCraft MVP

This slice adds two local-first runtime surfaces to Buddy Agent:

1. Buddy Training: a small persisted progression engine for Buddy growth.
2. AgentCraft bridge: an optional local HUD event bridge.

## Ownership

- `buddy-agent` owns executable runtime behavior, local state updates, and CLI commands.
- `buddy-brain` owns contracts, policy, and cross-repo source-of-truth docs.
- `prismtek-apps` owns app UI schemas and surfaces that display training state.
- AgentCraft is a visual HUD only. It is not runtime authority, approval state, durable memory, or persistence evidence.

## Commands

```bash
buddy agentcraft doctor
buddy agentcraft smoke
buddy agentcraft emit mission_start '{"name":"Buddy smoke"}'

buddy train status
buddy train reward quest_completed
buddy train reset
```

Use `--state` to point training commands at a temporary or app-managed state file:

```bash
buddy --state .tmp/buddy-training.json train reward quest_completed
```

## Safety defaults

The AgentCraft bridge is disabled unless explicitly enabled:

```bash
BUDDY_AGENTCRAFT_ENABLED=1 buddy agentcraft smoke
```

The bridge defaults to `http://localhost:2468/event`, rejects non-local endpoints, redacts prompt text by default, redacts secret-like fields, truncates command summaries, and never fails Buddy runtime work when AgentCraft is unavailable.

## Training model

Buddy Training stores local cosmetic/progression state:

- level
- xp and lifetime xp
- sparks and snacks
- stats: bond, focus, curiosity, discipline, creativity, reliability, autonomy
- achievements
- cosmetics
- evolution stage
- last action

The training state is not memory evidence and does not prove that runtime work completed. Real work still requires normal Buddy runtime receipts.

## MVP loop

```text
Buddy action -> local reward -> persisted training state -> optional AgentCraft HUD event -> app surface can render Buddy growth
```

The first app-facing loop should render Buddy as a safe companion/progression layer, not as a global activity tracker. App surfaces should use explicit Buddy events and consented app-local actions instead of raw keystrokes, global clicks, or hidden productivity monitoring.
