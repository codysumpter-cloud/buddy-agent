# Agent Life host

Buddy Agent can host the bounded developmental profile compiled by BUAP PR #35.

This is **functional affect**, not a claim that software is conscious. Drives, traits, preferences, relationships, and development influence host decisions while compiled permissions and constitutional policy remain immutable.

## Inputs and local state

The host consumes:

```text
.buddy/life-profile.json
```

It persists mutable state separately, by default under:

```text
~/.buddy_agent/agent-life/state.json
```

Raw `prismtek-agent-life-event-v1` records are published to:

```text
~/.buddy_agent/agent-life/outbox/
```

Knowledge Vault PR #7 validates and converts those files into graph memory.

Override the paths with `--state`, `--outbox`, `BUDDY_AGENT_LIFE_STATE`, or `BUDDY_AGENT_LIFE_OUTBOX`.

## Start the host

```bash
buddy-life --profile .buddy/life-profile.json status
```

The first invocation creates an atomic host document containing the runtime state and any memory events awaiting publication.

## Teach one evidenced outcome

```bash
buddy-life --profile .buddy/life-profile.json outcome \
  --id ci-run-123 \
  --kind task_succeeded \
  --subject-type tool \
  --subject-id github-actions \
  --reward 0.8 \
  --confidence 0.95 \
  --authority-kind verifier \
  --authority-id github-actions \
  --evidence receipt=run-123
```

Accepted outcomes update bounded state, atomically persist it, and publish one immutable event to the local Knowledge Vault outbox.

The agent cannot be its own authority. Evidence is mandatory unless the compiled profile explicitly says otherwise.

## Teach from Buddy task receipts

Task completion itself does not reward the agent. An external authority must admit a terminal task and cite sanitized evidence:

```bash
buddy-life --profile .buddy/life-profile.json task-outcome \
  task-0123456789abcdef01234567 \
  --authority-kind verifier \
  --authority-id github-actions \
  --evidence receipt=run-123 \
  --subject-id github-ci-recovery
```

Only completed or failed tasks are accepted. Cancelled, running, planned, or unprovenanced tasks cannot teach the agent.

The subject ID should name a reusable workflow or capability rather than a private path or one-off prompt.

## Explain and decay preferences

```bash
buddy-life --profile .buddy/life-profile.json preference tool github-actions
buddy-life --profile .buddy/life-profile.json advance 24
```

Preferences decay toward neutral, and drives and traits return toward their compiled baselines according to their configured half-lives.

## Crash recovery

Learning state and its pending memory event are committed together before publication. If the process stops between state persistence and outbox publication, the next host startup publishes the pending event idempotently and clears the marker.

```bash
buddy-life --profile .buddy/life-profile.json flush
```

Manual flushing is available, but ordinary startup performs the same recovery automatically.

## Safety and privacy

Do not include:

- raw prompts or private chain-of-thought;
- credentials, cookies, account identifiers, or private keys;
- private file paths;
- unredacted tool output;
- unrelated personal history.

Use stable receipt, run, artifact, or verification identifiers. The runtime state never contains the compiled constitution and can never expand permissions or replace safety policy.
