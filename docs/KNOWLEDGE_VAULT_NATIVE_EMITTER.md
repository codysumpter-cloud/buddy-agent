# Knowledge Vault Native Emitter: Buddy Agent

## Status

This document is a **native emitter specification only**. Buddy Agent does not yet include a production code adapter that writes directly into Knowledge Vault / Vegapunk Brain. Until that adapter exists and is reviewed, any emitted event is a drafted, reviewed artifact rather than automatic runtime output.

BUAP remains the profile and routing layer. Buddy Agent owns guarded task/action/runtime receipts and must not treat BUAP as the runtime owner.

## Source identity

- Source repo: `codysumpter-cloud/buddy-agent`
- Source name for Vegapunk Brain events: `buddy-agent`
- Receiver contract: `knowledge-vault/99-System/Vegapunk Brain/integrations/satellite-native-emitters.md`
- Receiver schema: `knowledge-vault/99-System/Vegapunk Brain/emitters/graph-event.schema.json`

## Emitter responsibility

Buddy Agent may emit public-safe event drafts for guarded runtime work:

- task and action receipts;
- worker reports and result summaries;
- approval-required pauses;
- denied or blocked actions;
- runtime/system state summaries that are safe to publish;
- durable concepts discovered while executing a task.

The emitter records what happened in sanitized receipt form. It does **not** export raw conversations, raw prompts, browser sessions, credentials, local paths, private workspace details, or live account state.

## Allowed event classes

Buddy Agent may draft the following event classes when they pass sanitization and approval rules:

| Event class | Typical Vegapunk event types | Purpose |
| --- | --- | --- |
| `task` | `task_created`, `task_completed` | Record started/completed guarded work and safe result summaries. |
| `system` | `repo_updated`, `feature_added`, `feature_removed`, `model_changed` | Record public-safe runtime, adapter, or repo capability changes. |
| `decision` | `decision_made` | Record execution decisions that are durable and safe to publish. |
| `concept` | `concept_created`, `concept_updated`, `relationship_created` | Record durable reusable concepts discovered during safe work. |

## Trigger points

Native emitter code, once implemented, should draft an event at these points:

1. **Session start** — only a public-safe session receipt, with no raw prompt or private operator context.
2. **Worker report** — summarized task progress and output facts, not hidden reasoning or transcripts.
3. **Approval-required pause** — sanitized description of the requested action, risk class, and blocked state.
4. **Completion** — sanitized result receipt, changed public files, validation summary, and known follow-ups.
5. **Denied action** — sanitized denial reason and risk class, without attempting the blocked action.

## Public-alpha safety policy

Buddy Agent must preserve the public-alpha risk policy:

- local/manual defaults stay conservative;
- `read-only` and `draft-only` work can be recorded after sanitization;
- `write`, `external-action`, `repo-mutation`, and `location` work requires confirmation before action and before durable emission when the event would affect governance or persistent public state;
- `credential`, `money`, `identity`, and destructive work remains deny-by-default unless a separately reviewed policy explicitly allows a safe draft-only record;
- denied actions may emit only a sanitized denial receipt.

## Never emit

The native emitter must reject or strip all of the following:

- secrets, tokens, API keys, cookies, private keys, OAuth material, passwords, or credentials;
- raw prompts, hidden reasoning, raw transcripts, private browser sessions, screenshots of private sessions, or page dumps;
- private local paths, personal machine names, account identifiers, or environment-specific absolute paths;
- live account control details, wallet material, trading instructions, deposits, withdrawals, gambling actions, or money movement instructions;
- unreviewed private Hermes/Buddy environment details;
- any data that would make the public Knowledge Vault a credential inventory or private activity log.

## Event draft shape

Emitter output should be an event JSON object that validates against `graph-event.schema.json` before intake:

```json
{
  "event_id": "evt-buddy-agent-task-example",
  "event_type": "task_completed",
  "source": "buddy-agent",
  "timestamp": "2026-06-15T00:00:00Z",
  "payload": {
    "class": "task",
    "summary": "Sanitized task receipt for public Knowledge Vault intake.",
    "receipts": ["public file path or commit reference only"],
    "risk_class": "repo-mutation",
    "approval_state": "approved",
    "adapter_status": "spec-only"
  }
}
```

The example above is intentionally fake and public-safe. Real adapter output must provide real receipt references without exposing private runtime data.

## Adapter requirements

Before Buddy Agent can be considered a complete native satellite emitter, it needs reviewed adapter code that:

1. builds event drafts from sanitized runtime receipts only;
2. validates every draft against Knowledge Vault's `graph-event.schema.json`;
3. blocks emission on sanitizer failure;
4. writes to the reviewed receiver intake path rather than directly mutating compiled graph outputs;
5. includes tests for secret stripping, private-path stripping, raw-prompt exclusion, denied-action receipts, and approval-required pauses.

Until then, this spec defines the contract and guardrails, not a live emitter implementation.
