# Buddy MCP task lifecycle tools

The packaged `buddy-mcp` runtime composes the original local context tools with the persistent `buddy.task.*` lifecycle.

## Tool surface

| Tool | Purpose |
|---|---|
| `buddy.task.create` | Create a persistent task identity and risk class. |
| `buddy.task.list` | List tasks newest-first. |
| `buddy.task.get` | Read one task, plan, approval, evidence references, and receipts. |
| `buddy.task.plan` | Add reviewable steps and verification commands. |
| `buddy.task.approval` | Record an attributable human approval or denial. |
| `buddy.task.start` | Move an approved/planned task to running; executes nothing itself. |
| `buddy.task.step` | Record a completed or failed step and artifact references. |
| `buddy.task.complete` | Complete only after every step and required evidence reference is present. |
| `buddy.task.cancel` | Cancel a non-terminal task. |
| `buddy.task.resume` | Resume a cancelled/failed task and re-request approval when required. |

## Local storage

When launched for a repository, MCP task state defaults to:

```text
<project>/.buddy/runtime/tasks/
<project>/.buddy/runtime/receipts/
```

Operators may override those paths with `BUDDY_TASKS_DIR` and `BUDDY_RECEIPTS_DIR`.

Runtime state is local and should not be committed. Repository policy and generated `.buddy` configuration remain separate from `.buddy/runtime/**`.

## Approval boundary

Planning `write`, `repo-mutation`, or `destructive` work creates an `awaiting_approval` task. The task cannot start until `buddy.task.approval` records:

- a boolean decision;
- `decided_by` attribution;
- decision time;
- optional note.

The lifecycle records approval but does not grant an executor broader filesystem, network, secret, production, or account permissions than its sandbox actually enforces.

## Execution boundary

These tools manage state and evidence references. They do **not**:

- run a shell command;
- modify a repository;
- launch Codex or another model;
- inspect artifact contents;
- access signed-in browser state;
- send messages or change external accounts.

A future executor must update this lifecycle rather than inventing separate task state. A future Mission Control surface can consume the same tools and records through the stable MCP transport.
