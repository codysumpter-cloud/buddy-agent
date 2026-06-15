# Buddy Agent Control Plane and Observability Integration

Status: initial live runtime adapter + integration contract  
Owner repo: `codysumpter-cloud/buddy-agent`  
Related receiver: `codysumpter-cloud/knowledge-vault` / `99-System/Vegapunk Brain/`  
Reference systems: AgentRQ, Monocle

## Purpose

Buddy Agent is the runtime executor for guarded user tasks. This document defines and tracks the first live adapter layer for:

- AgentRQ-style task, reply, and approval control-plane operations.
- Monocle-style private trace setup and sanitized trace summaries.
- Knowledge Vault / Vegapunk Brain sanitized runtime receipt emission.

The first adapter lives under `src/buddy_agent/control_plane/`. It is intentionally small, stdlib-only, and credential-free. It can be called by the existing Buddy runtime loop by injecting an AgentRQ/MCP tool transport.

## Implementation status

Implemented in this PR:

| File | Runtime role |
| --- | --- |
| `src/buddy_agent/control_plane/agentrq.py` | Allowlisted AgentRQ MCP-style client for workspace/task/status/reply operations. |
| `src/buddy_agent/control_plane/monocle.py` | Optional lazy Monocle setup and private trace summary builder. |
| `src/buddy_agent/control_plane/knowledge_vault.py` | Sanitized Knowledge Vault event builder/writer for inbox event drafts. |
| `src/buddy_agent/control_plane/runtime_adapter.py` | High-level coordinator for AgentRQ task state, Monocle summaries, and Knowledge Vault events. |
| `src/buddy_agent/control_plane/sanitizer.py` | Conservative redaction and unsafe-data blocking. |
| `tests/test_control_plane_runtime_adapter.py` | Tests for task completion, redaction, raw trace blocking, denied approval handling, and attachment denial. |

Not implemented in this PR:

- Real AgentRQ credentials or committed MCP config.
- Direct network calls to AgentRQ.
- Raw Monocle trace export.
- Automatic cross-repo writes into `knowledge-vault`.
- Compiled graph mutation.

## Why these two systems fit Buddy Agent

AgentRQ exposes a realtime task workspace where agents can retrieve assigned tasks, update task statuses, reply to task threads, request permissions, and work through MCP-compatible tools.

Monocle traces GenAI app and agent execution using OpenTelemetry-compatible spans. Buddy Agent treats raw traces as private runtime artifacts and emits only sanitized trace summaries.

## Integration roles

| System | Buddy Agent role | Durable memory status |
| --- | --- | --- |
| AgentRQ | Optional task, reply, and approval control plane | Only sanitized task receipts may be emitted. |
| Monocle | Optional private trace recorder and verification source | Raw traces must not be emitted. |
| Knowledge Vault | Durable graph/memory receiver | Receives sanitized graph events only. |

## Runtime adapter flow

```text
AgentRQ injected MCP/tool transport
  -> AgentRQClient.get_next_task()
  -> ControlPlaneRuntimeAdapter.run_next_task(runner)
  -> MonocleAdapter optional setup + private trace summary
  -> Sanitizer strips or blocks unsafe data
  -> KnowledgeVaultEmitter builds schema-shaped event
  -> caller may write the event to an approved Knowledge Vault inbox path
```

The adapter requires the caller to inject the AgentRQ transport. That keeps `.mcp.json`, `.codex/config.toml`, OAuth credentials, bearer tokens, and tokenized MCP URLs outside the repo.

## AgentRQ adapter contract

Allowed operations:

- Read workspace task state.
- Pull the next task assigned to Buddy Agent.
- Post task progress replies.
- Update task status through `notstarted`, `ongoing`, `blocked`, and `completed`.
- Surface approval-required pauses to the human operator.
- Record allow/deny outcomes as sanitized receipts.
- Download attachments only when explicitly enabled by caller policy.

Blocked by default:

- Attachment downloads.
- Unknown AgentRQ tools.
- Unsupported task statuses.
- Silent approval. Silence is never approval.
- Tokenized URL persistence.
- Raw AgentRQ task chat persistence.

## Monocle adapter contract

The Monocle adapter imports `monocle_apptrace` lazily only when enabled. If Monocle is unavailable, startup returns a public-safe `unavailable` status instead of crashing the Buddy runtime.

Allowed Monocle uses:

- Private trace setup.
- Duration/error/status summaries.
- Tool category summaries.
- Trace assertions such as `no_secrets_emitted` and `no_raw_prompt_emitted`.

Blocked durable outputs:

- raw OpenTelemetry spans
- prompts
- full model outputs
- tool arguments
- tool outputs
- local/private paths
- browser sessions
- credentials, headers, cookies, and API keys

## Knowledge Vault receipt contract

The runtime adapter builds Knowledge Vault-shaped event drafts with required fields:

- `event_id`
- `event_type`
- `source`
- `timestamp`
- `payload`

The emitter never writes to compiled graph outputs. It can only write to a caller-supplied inbox directory and rejects duplicate event IDs.

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

## Validation

Run the adapter tests with:

```bash
python -m pytest tests/test_control_plane_runtime_adapter.py
```

The tests prove:

- AgentRQ task state can move `notstarted -> ongoing -> completed`.
- Sanitized Knowledge Vault events are generated.
- tokenized URLs and secret-like values are not persisted.
- raw trace markers and raw prompt/conversation fields are blocked.
- attachment downloads are denied by default.
- silence cannot be treated as approval.
