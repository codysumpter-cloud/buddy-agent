# Buddy + Lil' Buddy Runtime Scaffold

Status: alpha scaffold
Owner: buddy-agent
Last verified: 2026-06-12

## Purpose

This repo owns the runnable local execution surface for the Buddy + Lil' Buddy standard.

The scaffold implements compatible concepts only:

- Buddy orchestrator
- Lil' Buddy worker
- task envelopes
- result envelopes
- review envelopes
- tool contracts
- guardrails
- a local demo command that requires no paid APIs or secrets

It does not replace existing `runtime/action_loop.py`, providers, skills, receipts, or app bridges.

## Default flow

```text
Human prompt -> Buddy short plan -> task envelope -> Lil' Buddy worker -> result envelope -> Buddy Review -> final response
```

## Files

| Path | Purpose |
|---|---|
| `src/buddy_agent/orchestration/envelopes.py` | Task, result, review, and trace dataclasses |
| `src/buddy_agent/orchestration/orchestrator.py` | Buddy plan/delegate/review/respond scaffold |
| `src/buddy_agent/orchestration/worker.py` | Lil' Buddy scoped local worker scaffold |
| `src/buddy_agent/orchestration/demo.py` | `buddy-demo` CLI entry point |
| `schemas/buddy-task-envelope.schema.json` | JSON Schema for task envelopes |
| `schemas/buddy-result-envelope.schema.json` | JSON Schema for result envelopes |

## Local demo

Run after installing the package locally:

```bash
buddy-demo "Draft a safe project note"
```

Equivalent module call from a checkout:

```bash
python -m buddy_agent.orchestration.demo "Draft a safe project note"
```

The command prints JSON with:

- `buddy_plan`
- `task`
- `result`
- `review`
- `final_response`
- `system_prompt_template`
- `durable_memory_targets`

The demo is deterministic, local-only, and uses no network provider.

## Tool contracts

Lil' Buddy can use tools only through the contracts Buddy grants in a task envelope. The local demo grants one `draft-only` tool named `local_reasoning`.

Supported contract labels:

- `read-only`
- `draft-only`
- `local-execution`
- `repo-mutation`
- `device-observation`
- `device-action`
- `external-action`

## Safety posture

The scaffold classifies obvious risk terms as `medium`, `high`, or `blocked`. High-risk tasks still return a local trace, but Buddy Review marks them as requiring approval before action.

Blocked examples include prompts that ask to bypass safety or ignore review.

## Ecosystem routing

| Concern | Owner |
|---|---|
| Durable standards | `knowledge-vault/99-System/Buddy Standards/` |
| Governance and prompt rules | `buddy-brain/context/council/` and `context/prompt-governance/` |
| Runtime scaffolds and demo | `buddy-agent/src/buddy_agent/orchestration/` |
| Local embodied/device events | `omni-buddy/docs/BUDDY_LIL_BUDDY_DEVICE_ROUTING.md` |

## Non-goals

This scaffold does not:

- require OpenAI or paid APIs
- perform external actions
- mutate repos
- execute arbitrary tools
- bypass existing Buddy Agent policies
- claim full compatibility with any external orchestration framework
