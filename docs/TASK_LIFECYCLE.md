# Buddy Task Lifecycle v1

Buddy tasks now have persistent identities and explicit state transitions independent of any provider or sandbox.

## Commands

```bash
buddy-task create "Fix issue #42" --risk repo-mutation --project-root .
buddy-task plan TASK_ID \
  --step "Inspect repository instructions and reproduce the issue" \
  --step "Implement the smallest durable fix" \
  --step "Run repository-native verification" \
  --verify "pytest -q" \
  --verify "ruff check ."
buddy-task approve TASK_ID --by "Cody" --note "Approved for this branch"
buddy-task start TASK_ID
buddy-task step-complete TASK_ID step-1 --detail "Issue reproduced"
buddy-task step-complete TASK_ID step-2 --detail "Patch written"
buddy-task step-complete TASK_ID step-3 \
  --detail "Required checks passed" \
  --artifact artifacts/pytest.log \
  --artifact artifacts/ruff.log
buddy-task complete TASK_ID "Issue fixed and verified"
```

Other lifecycle commands:

```text
list
status
approve / deny
cancel / resume
fail
step-fail
```

## State model

```text
created
  → planned
  → awaiting_approval → planned | cancelled
  → running
  → completed | failed | cancelled

failed | cancelled → resume → planned | awaiting_approval
```

`write`, `repo-mutation`, and `destructive` tasks request attributable human approval when planned. `destructive` remains a lifecycle classification only; this feature does not add an executor that can perform destructive work.

## Verification boundary

A task cannot be marked completed until:

- every planned step is completed;
- the completion summary is non-empty;
- any step carrying verification commands records artifact paths for the evidence.

Artifact paths are evidence references, not proof that Buddy independently inspected their contents. Sandbox execution and artifact verification are separate follow-up layers and must use this lifecycle rather than bypassing it.

## Persistence and recovery

Each task is stored as `buddy.task.v1` JSON under:

```text
${BUDDY_TASKS_DIR:-~/.buddy_agent/tasks}/task-<id>.json
```

Writes use an fsynced temporary file and atomic replacement. A new process can load the same task identity, plan, approval state, step progress, receipts, and revision.

## Receipts and privacy

Pass `--receipts-dir PATH` to emit the existing sanitized Buddy JSONL receipts. Lifecycle receipts contain task ID, state, risk, revision, and local state path. They intentionally exclude the raw objective, approval note, step detail, prompts, credentials, browser state, and tool outputs.

## Current boundary

Implemented:

- persistent task IDs;
- plan and step state;
- attributable approval and denial;
- cancel, fail, and resume;
- evidence-gated completion;
- sanitized lifecycle receipts;
- CLI and library API.

Not implemented by this module:

- shell or repository execution;
- container/worktree sandbox enforcement;
- provider invocation;
- HTTP/WebSocket service transport;
- MCP task tools;
- automatic KnowledgeVault events;
- Mission Control UI.
