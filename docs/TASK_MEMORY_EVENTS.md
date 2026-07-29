# Persistent task → Vegapunk Brain events

The composed `buddy-mcp` runtime can emit public-safe task lifecycle events into a local KnowledgeVault/Vegapunk inbox.

Configure the receiver explicitly:

```bash
export BUDDY_VAULT_INBOX="/path/to/knowledge-vault/99-System/Vegapunk Brain/inbox/events"
buddy-mcp
```

When the variable is absent, task mutations still succeed and return:

```json
{
  "memory_event": {
    "configured": false,
    "emitted": false,
    "event_type": null,
    "event_id": null,
    "error": null
  }
}
```

## Event mapping

| MCP action | Vegapunk event |
|---|---|
| `buddy.task.create` | `task_created` |
| `buddy.task.complete` | `task_completed` |
| plan, approval, start, step, cancel, resume | `task_state_changed` |

Each mutation returns `memory_event` metadata showing whether emission was configured and successful. A failed inbox write does not erase the already-persisted local task, but the failure is explicit so operators can repair and replay it later.

## Public-safe payload

Events contain only:

- task ID;
- previous/current status;
- risk class;
- task revision;
- approval required/decision state;
- counts of pending, running, completed, failed, and skipped steps;
- receipt count;
- sanitized lifecycle summary and action name;
- public-safe Buddy Agent source reference.

Events do **not** contain:

- raw task objective;
- approval actor or note;
- step titles or details;
- verification commands;
- artifact paths;
- prompts or model output;
- tool arguments/output;
- credentials or secret values;
- browser state;
- private project/vault paths;
- source excerpts.

## Claim boundary

`task_created`, `task_state_changed`, and `task_completed` describe durable lifecycle state. They do not prove that a real artifact was executed or verified.

`execution_verified` remains a separate, stronger Trust Fabric event and may be emitted only after Buddy verifies a real artifact and required security/test gates.

## Receiver contract

KnowledgeVault schema support for `task_state_changed` was added first in `codysumpter-cloud/knowledge-vault#5`. Buddy Agent should not claim event compatibility against an older vault schema.
