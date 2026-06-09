# Buddy Product Spine

Buddy Product Spine is the runtime-facing contract that ties Prismtek Apps, Buddy Agent, and Buddy Brain into one product loop.

## Why this exists

Buddy had useful pieces spread across repos:

- a guarded Agent Browser and `.bemore` workspace runtime in `prismtek-apps`;
- local runtime, app-chat, Game Studio, and `.buddy/playground` in `buddy-agent`;
- browser automation policy and workspace dispatch in `buddy-brain`.

The product spine gives those pieces one shared map so the app, runtime, and operator policy can agree on ownership, flow, risk, and artifact paths.

## CLI

```bash
buddy-product-spine summary
buddy-product-spine json
buddy-product-spine validate
```

`summary` is for humans. `json` is for app/runtime consumers. `validate` is the CI-friendly check.

## Source of truth

The machine-readable implementation lives in:

```text
src/buddy_agent/product_spine.py
```

The CLI wrapper lives in:

```text
src/buddy_agent/cli_product_spine.py
```

Tests live in:

```text
tests/test_product_spine.py
```

## Product loop

```text
Human
  -> Guarded Agent Browser in prismtek-apps
  -> Buddy Orchestrator / Workspace Dispatch in buddy-brain
  -> Lil' Buddy Worker drafts in .buddy/playground
  -> Buddy Agent validates local runtime/app-chat/integrations
  -> Prismtek Apps promotes approved outputs into .bemore
  -> external adapters act only after approval
```

## Workspace split

| Workspace | Owner | Purpose |
| --- | --- | --- |
| `.bemore/` | `prismtek-apps` | App-visible runtime artifacts, skills, receipts, memory, session state, and action logs. |
| `.buddy/playground/` | `buddy-agent` | Local/project drafts, browser notes, code tasks, art requests, outbox drafts, pre-adapter receipts. |

Promotion from `.buddy/playground/` into `.bemore/` must be explicit, reviewable, and receipt-backed.

## Approval boundary

Approval is required for:

- `write`
- `external-action`
- `destructive`
- `credential`
- `money`
- `repo-mutation`

Unknown risk classes must stop the loop until classified.

## App-side mirror

`prismtek-apps` mirrors this contract in:

```text
packages/core/buddyProductSpine.ts
```

That lets the product UI inspect/render the same surfaces and approval rules that Buddy Agent validates.

## Operator-side mirror

`buddy-brain` mirrors this contract in:

```text
docs/BUDDY_PRODUCT_SPINE.md
```

That gives Workspace Dispatch and browser policy a single map for product-level routing.
