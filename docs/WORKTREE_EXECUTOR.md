# Git worktree executor v1

`buddy-exec` runs a reviewed command plan on a dedicated branch and git worktree after the corresponding Buddy task is already `running` and any required human approval is recorded.

## Example

Create and approve the task first:

```bash
TASK_ID="$(buddy-task create "Run repository verification" \
  --risk repo-mutation --project-root . | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"

buddy-task plan "$TASK_ID" \
  --step "Run repository-native checks" \
  --step "Review generated diff" \
  --verify "pytest -q"

buddy-task approve "$TASK_ID" --by "Cody"
buddy-task start "$TASK_ID"
```

Create a reviewable execution plan:

```json
{
  "base_ref": "HEAD",
  "keep_worktree": true,
  "commands": [
    {"argv": ["python", "-m", "pytest", "-q"], "timeout_seconds": 900},
    {"argv": ["git", "status", "--short"], "timeout_seconds": 30}
  ]
}
```

Run it:

```bash
buddy-exec run "$TASK_ID" --repository . --plan execution-plan.json
```

Review the worktree and evidence, then clean up explicitly:

```bash
buddy-exec cleanup "$TASK_ID" --repository .
```

The branch remains by default. Add `--delete-branch` only after reviewing and preserving any wanted work.

## What is technically enforced

- a dedicated `buddy/<task-id>` git branch and worktree;
- source repository files are not directly mutated;
- task must exist and be in `running` state;
- required lifecycle approval must be recorded;
- direct `subprocess` argv execution with `shell=False`;
- executable allowlist;
- git commands limited to read-only `status`, `diff`, `show`, `log`, and `rev-parse`;
- command working directory must remain inside the worktree;
- inherited environment is reduced to basic platform/path variables;
- no secret environment injection;
- timeout and captured stdout/stderr for every command;
- sanitized logs, status, binary patch, diff stat, hashes, capabilities, and limitations.

## What is **not** enforced

This executor is **not an operating-system or container sandbox**.

- child processes can potentially read other host files;
- child processes can potentially use the host network;
- repository scripts may execute arbitrary code through an allowlisted package manager;
- no scoped secret access is supported;
- no production, account, message, calendar, payment, or deployment action is granted.

Every evidence record reports these limitations and sets `host_filesystem_isolation`, `network_isolation`, and `scoped_secrets_supported` to `false`.

Use this only for trusted repositories and reviewed command plans. The separate Docker/container provider is required before Buddy can claim enforced host and network isolation.

## Evidence

The default paths are:

```text
~/.buddy_agent/worktrees/<task-id>/
~/.buddy_agent/executions/<task-id>/
```

Execution evidence includes:

```text
execution-evidence.json
command-XX.stdout.log
command-XX.stderr.log
git-status.txt
changes.patch
diff-stat.txt
```

Do not put credentials, tokens, passwords, or private keys in command arguments or execution-plan files. This version deliberately does not provide secret injection.
