# Agent Readiness Layer

Buddy Agent owns executable contracts and sanitized evidence. Buddy Brain owns cross-repository scoring and routing analysis. BUAP owns canonical instruction compilation.

## Sandbox contract

The default request is conservative:

```text
network: none
filesystem: workspace-write
secrets: none
```

Repository profiles may expand permissions only through explicit policy. `coding`, `review`, and `release` are separate profiles. Release requires human approval and scoped secrets.

A provider must declare what it actually enforces. Prompt instructions and environment flags are not accepted as proof of network or filesystem isolation. `PolicyOnlySandboxProvider` deliberately refuses live creation until a real provider adapter is implemented and audited.

```bash
buddy-readiness sandbox profiles
buddy-readiness sandbox plan local-container review
```

## Security evidence

Security gates retain check name, rule, severity, confidence, resolution, and evidence reference. Unresolved high-severity/high-confidence findings block. Unresolved medium-severity/high-confidence findings require review. Missing required checks also require review.

```bash
buddy-readiness security gate security-evidence.json
```

This complements CodeQL, dependency scanning, language static analysis, tests, and secret scanning; it does not replace them.

## Cost-to-verified-completion telemetry

`TaskEconomics` records attempts, model/tool cost, elapsed time, human review time, verification, artifact acceptance, rollback, and security gate without recording prompts, secrets, or browser state. Buddy Brain can aggregate these JSONL records by provider and model.

## External agent session receipts

Codex, Copilot, VS Code, and other execution hosts may export a sanitized `buddy.external-agent-session.v1` document. Buddy validates the document and converts it into its normal receipt stream:

```bash
buddy-readiness external-session external-session.json
```

The import preserves:

- provider, harness, model, and external session identity;
- logical repository, branch, and worktree references;
- visible subagent spans;
- tool names, call IDs, statuses, resource references, timing, and optional argument/result hashes;
- commit SHAs and pull-request reference;
- named verification evidence and observation timestamps;
- a deterministic hash of the sanitized source receipt.

The import rejects raw prompts, conversation messages, raw tool inputs or outputs, browser state, credentials, secret-like fields, absolute host paths, escaping references, duplicate call/span IDs, and invalid commit or SHA-256 values. A completed external session receives `ok` only when it includes verification evidence and every verification record passed. Missing or pending verification remains `review`; failed verification becomes `error`.

A worktree reference is evidence of Git-state isolation only. It is not recorded or described as a security sandbox.

## Checkpoint and edge-runtime contract

```bash
buddy-readiness checkpoint smoke
```

The smoke sequence starts a run, executes a tool, serializes state, restores it, continues, verifies cumulative usage and trace identity, and confirms lifecycle listeners are released. Hosted multi-agent behavior remains disabled by default until a real provider adapter passes cancellation, nested-failure, trace-propagation, and accounting tests.
