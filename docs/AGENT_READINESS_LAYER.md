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

A provider must declare what it actually enforces. Prompt instructions and environment flags are not accepted as proof of network or filesystem isolation. `PolicyOnlySandboxProvider` deliberately refuses live creation.

`LocalContainerSandboxProvider` is the first executable adapter. It uses Docker or Podman with:

- one explicit bind-mounted workspace;
- a read-only container root filesystem;
- `network=none` enforcement when requested;
- all Linux capabilities dropped and `no-new-privileges` enabled;
- bounded CPU, memory, process count, and command duration;
- no engine socket mount and no implicit host environment inheritance;
- explicit scoped-secret injection through a temporary mode-`0600` environment file;
- host-side workspace snapshots and restoration;
- whole-container destruction when a command times out.

The first adapter intentionally reports hostname allowlists as unsupported. `coding` and `release` remain non-executable with this provider until an audited proxy or equivalent enforcement layer exists. The network-free `review` profile is executable.

```bash
buddy-readiness sandbox profiles
buddy-readiness sandbox plan local-container review
buddy-readiness sandbox plan local-container coding  # expected to refuse network:allowlist
buddy-readiness sandbox self-test local-container /path/to/workspace
```

The live self-test uses a temporary child workspace and checks command execution, network isolation, host-secret non-inheritance, scoped workspace writes, checkpoint restoration, container cleanup, and process-tree termination on timeout. It requires a healthy Docker or Podman daemon and the default Python container image unless the adapter is configured programmatically with another compatible image.

## Security evidence

Security gates retain check name, rule, severity, confidence, resolution, and evidence reference. Unresolved high-severity/high-confidence findings block. Unresolved medium-severity/high-confidence findings require review. Missing required checks also require review.

```bash
buddy-readiness security gate security-evidence.json
```

This complements CodeQL, dependency scanning, language static analysis, tests, and secret scanning; it does not replace them.

## Cost-to-verified-completion telemetry

`TaskEconomics` records attempts, model/tool cost, elapsed time, human review time, verification, artifact acceptance, rollback, and security gate without recording prompts, secrets, or browser state. Buddy Brain can aggregate these JSONL records by provider and model.

## Checkpoint and edge-runtime contract

```bash
buddy-readiness checkpoint smoke
```

The smoke sequence starts a run, executes a tool, serializes state, restores it, continues, verifies cumulative usage and trace identity, and confirms lifecycle listeners are released. Hosted multi-agent behavior remains disabled by default until a real provider adapter passes cancellation, nested-failure, trace-propagation, and accounting tests.
