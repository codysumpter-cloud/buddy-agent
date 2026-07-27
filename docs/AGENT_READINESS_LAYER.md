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

## Checkpoint and edge-runtime contract

```bash
buddy-readiness checkpoint smoke
```

The smoke sequence starts a run, executes a tool, serializes state, restores it, continues, verifies cumulative usage and trace identity, and confirms lifecycle listeners are released. Hosted multi-agent behavior remains disabled by default until a real provider adapter passes cancellation, nested-failure, trace-propagation, and accounting tests.
