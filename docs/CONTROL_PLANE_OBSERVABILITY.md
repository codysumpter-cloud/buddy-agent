# Buddy Agent Control Plane and Observability Integration

Status: spec-only integration contract  
Owner repo: `codysumpter-cloud/buddy-agent`  
Related receiver: `codysumpter-cloud/knowledge-vault` / `99-System/Vegapunk Brain/`  
Reference systems: AgentRQ, Monocle

## Purpose

Buddy Agent is the runtime executor for guarded user tasks. This document defines how Buddy Agent should integrate with:

- AgentRQ as an optional human-in-the-loop task and approval control plane.
- Monocle as an optional trace and verification layer for agent/tool execution.
- Knowledge Vault / Vegapunk Brain as the durable sanitized receipt receiver.

This is not a live adapter yet. It is the contract future adapter code must satisfy before Buddy Agent can claim native AgentRQ or Monocle support.

## Why these two systems fit Buddy Agent

AgentRQ exposes a realtime task workspace where agents can retrieve assigned tasks, update task status, reply to task threads, request permission for sensitive actions, and work through MCP-compatible tools. Buddy Agent can treat that as an operator-facing task queue and approval surface.

Monocle traces GenAI app and agent execution using OpenTelemetry-compatible spans. It can capture agent runs, tool calls, LLM calls, vector lookups, errors, timing, and trace-based test assertions. Buddy Agent can treat that as private runtime observability.

## Integration roles

| System | Buddy Agent role | Durable memory status |
| --- | --- | --- |
| AgentRQ | Optional task, reply, and approval control plane | Only sanitized task receipts may be emitted |
| Monocle | Optional private trace recorder and verification source | Raw traces must not be emitted |
| Knowledge Vault | Durable graph/memory receiver | Receives sanitized graph events only |

## AgentRQ adapter contract

Buddy Agent may use AgentRQ when a workspace is explicitly configured by the operator.

Allowed AgentRQ operations:

- Read workspace task state.
- Pull the next task assigned to Buddy Agent.
- Post task progress replies.
- Update task status through the approved lifecycle.
- Surface approval-required pauses to the human operator.
- Record allow/deny outcomes as sanitized receipts.
- Download attachments only when the task policy allows it.

Buddy Agent must not:

- Store AgentRQ tokens in repository files.
- Commit `.mcp.json`, `.codex/config.toml`, local settings, OAuth tokens, bearer tokens, workspace URLs containing tokens, or generated secrets.
- Treat AgentRQ approval as permission to bypass Buddy Agent risk policy.
- Emit raw AgentRQ task messages, attachments, private workspace IDs, or tokenized URLs into Knowledge Vault.
- Turn on broad `allow_all_commands` behavior without a separate explicit human approval record.

Recommended local-only configuration paths:

```text
.mcp.json                 # local only, ignored by git
.codex/config.toml        # local only, ignored by git
.claude/settings.local.json
.env.local
```

## Buddy Agent task lifecycle mapping

| Buddy Agent state | AgentRQ state | Knowledge Vault event class |
| --- | --- | --- |
| Session/task discovered | `notstarted` | `task` |
| Work accepted | `ongoing` | `task` |
| Missing approval | `blocked` | `decision` |
| Human denies risky action | `blocked` or `completed` with denial note | `decision` |
| Work completed | `completed` | `task` |
| Runtime/system issue | `blocked` | `system` |

## Monocle adapter contract

Buddy Agent may use Monocle to trace agent execution, but raw trace files are private runtime artifacts.

Allowed Monocle uses:

- Capture runtime span timelines for debugging.
- Verify expected tool calls in tests.
- Verify disallowed tools were not called.
- Track duration, error states, and validation outcomes.
- Produce local trace JSON files or send traces to an explicitly configured private observability backend.
- Summarize traces into sanitized receipts for Knowledge Vault.

Buddy Agent must not emit raw Monocle traces to Knowledge Vault.

Raw trace fields considered private by default:

- prompts and full model responses
- tool arguments and tool outputs
- file paths
- repo checkout paths
- browser sessions
- user IDs, tenant IDs, session IDs
- tokens, headers, credentials, cookies
- attachment contents
- private conversation text
- raw stack traces that expose private paths or secrets

## Sanitized receipt shape

Buddy Agent may convert AgentRQ state and Monocle traces into a Knowledge Vault event only after sanitization.

```json
{
  "source": "buddy-agent",
  "event_class": "task",
  "title": "Completed guarded repository task",
  "summary": "Buddy Agent completed a docs-only integration task and recorded validation status.",
  "task_ref": "public-pr-or-issue-reference",
  "control_plane": {
    "provider": "agentrq",
    "workspace_ref": "redacted-or-public-alias",
    "task_status": "completed",
    "approval_required": false,
    "approval_outcome": "not_required"
  },
  "observability": {
    "provider": "monocle",
    "trace_ref": "private-trace-id-or-redacted",
    "raw_trace_exported": false,
    "assertions": [
      "no_secrets_emitted",
      "no_raw_prompt_emitted",
      "validation_completed"
    ]
  },
  "validation": {
    "status": "passed",
    "commands": [
      "docs-only review"
    ]
  },
  "redaction": {
    "raw_prompts": "excluded",
    "secrets": "excluded",
    "private_paths": "excluded",
    "browser_sessions": "excluded"
  }
}
```

## Required guardrails

Every adapter implementation must preserve the existing public-alpha risk policy:

- Risky actions require explicit approval before execution.
- Approval requests must describe the action, scope, expected effect, rollback path, and risk.
- Denied actions must be recorded as denied, not silently retried.
- Secrets and credentials must never be logged, emitted, or committed.
- Browser/session data must never become durable public memory.
- Raw prompts must never become durable public memory.
- Private file paths must be redacted before receipts are emitted.
- Knowledge Vault receives receipts, not raw runtime dumps.

## Implementation status

Current status: spec-only.

Buddy Agent is not AgentRQ-native or Monocle-native until a reviewed adapter exists with:

- local-only config loading
- token redaction
- task lifecycle mapping
- approval pause handling
- Monocle trace capture
- trace-to-receipt sanitization
- schema validation against `knowledge-vault/99-System/Vegapunk Brain/emitters/graph-event.schema.json`
- tests proving private fields are not emitted

## Minimum future implementation plan

1. Add local configuration discovery for optional AgentRQ workspace endpoints.
2. Add an AgentRQ client wrapper with explicit allowlisted operations.
3. Add Monocle setup behind an opt-in environment flag.
4. Add a trace sanitizer that emits only summary-level assertions.
5. Add a Knowledge Vault emitter adapter that validates events against the receiver schema.
6. Add tests for secret redaction, prompt exclusion, denied approval handling, and schema validity.
7. Document setup without committing any tokenized config.

## Validation for this spec

- Documentation-only change.
- No runtime code is changed.
- No config file containing tokens is added.
- No generated trace or task data is committed.
- Integration remains explicitly optional and spec-only.
