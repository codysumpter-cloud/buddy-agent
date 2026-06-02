# Buddy Action Adapter Contract

Buddy-Agent is the guarded execution boundary for Buddy actions from Prismtek apps. This contract defines how the app-side `BuddyAction` and two-agent Orchestrator/Worker loop should land in the runtime without turning the public alpha into an unsupervised browser bot or live-account automation layer.

Status: design contract for public alpha. This document does not enable network actions by itself.

## Goal

Accept typed Buddy sessions, delegations, action drafts, and worker reports from trusted Prismtek surfaces; classify risk; require approval where needed; and return sanitized receipts.

```text
Prismtek App
  -> BuddyAgentSession v1
  -> Orchestrator receives human request
  -> Orchestrator delegates safe next step to Worker
  -> Worker performs allowed BuddyAction(s)
  -> Worker reports completion/blocker to Orchestrator
  -> Orchestrator continues, completes, or asks human for approval
  -> Buddy-Agent validation / risk policy
  -> sanitized BuddyReceipt
```

## Minimum complete runtime shape

Buddy-Agent is not complete as a useful agent runtime unless it supports at least two cooperating agent roles:

| Role | Runtime responsibility | Human contact | Tool execution |
| --- | --- | --- | --- |
| Orchestrator | Own the human's original request, plan/decompose steps, delegate to worker, receive reports, continue the loop, and request human approval when risk requires it. | Yes | Limited / policy-driven |
| Worker | Execute delegated safe steps, use tools within policy, report every completed step, and stop when an approval-required action is needed. | No by default | Yes, bounded by policy |

The Worker should not repeatedly ask the human what to do next. It reports to the Orchestrator. The Orchestrator reprompts the Worker using the human's original request, current progress, receipts, and the next safe instruction.

## Schema versions

Buddy-Agent should accept action payloads that declare:

```text
schemaVersion = 2026-06-02.buddy-action.v1
```

Buddy-Agent should accept session payloads that declare:

```text
schemaVersion = 2026-06-02.buddy-agent-session.v1
```

The matching app-side contract currently lives in `prismtek-apps` as:

```text
vendor/buddy-core-contracts/src/actions/BuddyActionLoop.ts
```

A future canonical package can replace the vendored snapshot once package auth and release flow are stable.

## Runtime loop

```text
1. Human gives task to Orchestrator.
2. Orchestrator creates BuddyAgentSession.
3. Orchestrator creates BuddyDelegation for Worker.
4. Worker executes safe read-only/draft-only actions.
5. Worker emits BuddyWorkerReport after each step.
6. Orchestrator decides next instruction.
7. Loop continues without human interruption while risk policy allows it.
8. If Worker needs write/external/destructive/money/identity/location/credential/repo-mutation action, it stops and reports `needs-approval`.
9. Orchestrator presents approval request to human.
10. If approved, Orchestrator resumes Worker with bounded next step. If denied, Orchestrator replans or stops.
```

## Accepted action classes for public alpha

| Action type | Risk | Public-alpha behavior |
| --- | --- | --- |
| `browser.open` | `read-only` | Allow only app-side guarded browser navigation. Runtime does not control signed-in browser sessions. |
| `browser.summarize` | `read-only` | Allow draft summary generation through local/offline or explicitly configured provider. |
| `memory.remember` | `draft-only` | Create a local memory draft/receipt. KnowledgeVault writes require a future audited adapter. |
| `memory.recall` | `read-only` | Allow local memory recall. External vault reads require explicit adapter approval. |
| `note.draft` | `draft-only` | Prepare note content only. No silent write to Apple Notes or external apps. |
| `calendar.draft` | `draft-only` | Prepare calendar event draft only. EventKit creation remains app/user reviewed. |
| `message.draft` | `draft-only` | Prepare message draft only. No silent sending. |
| `email.draft` | `draft-only` | Prepare email draft only. No silent sending. |
| `github.inspect` | `read-only` | Inspect public or explicitly authorized repo metadata. No mutation. |
| `github.pr.prepare` | `repo-mutation` | Confirm before branch/commit/PR creation. No default public-alpha mutation. |
| `sandbox.inspect` | `read-only` | Allow local/static inspection when sandbox is configured. |
| `sandbox.command` | `external-action` | Confirm before command execution; deny destructive commands by default. |
| `skill.invoke` | skill-defined | Use skill manifest risk policy. Unknown or missing manifest is denied. |

## Risk policy

Public-alpha default policy must match the app contract:

| Risk class | Default |
| --- | --- |
| `read-only` | allow |
| `draft-only` | allow |
| `write` | confirm |
| `external-action` | confirm |
| `destructive` | deny-by-default |
| `money` | deny-by-default |
| `identity` | deny-by-default |
| `location` | confirm |
| `credential` | deny |
| `repo-mutation` | confirm |

## Explicit non-goals

The public alpha must not add default support for:

- silent message sending
- silent email sending
- signed-in Safari/session automation
- hidden browser automation
- credential inventory
- scraping tokens, cookies, private keys, OAuth material, or browser sessions
- wallet signing
- deposits or withdrawals
- trading, gambling, prediction-market execution, or money-action execution
- destructive file/repo/system mutation without explicit approval
- Worker-to-human direct contact by default
- autonomous work without worker reports, receipts, and visible state

## Future CLI shape

The public-safe CLI shape can be added later as a reviewable surface:

```bash
buddy sessions start ./task.json --dry-run
buddy sessions report ./worker-report.json
buddy actions validate ./action.json
buddy actions submit ./action.json --dry-run
buddy actions receipts --latest
```

Initial implementation should prefer `--dry-run` and local receipt output over real adapter execution.

## Future local API shape

A local-only API may eventually expose:

```text
POST /buddy/sessions
POST /buddy/sessions/:id/delegations
POST /buddy/actions
POST /buddy/worker-reports
GET /buddy/actions/:id
GET /buddy/receipts
```

Requirements before enabling any local API:

- bind to localhost by default
- require explicit opt-in
- reject unknown schema versions
- validate action risk before dispatch
- redact receipt content
- include session, delegation, agent role, provider, and adapter IDs in receipts
- disable write/external/repo actions unless approval mode permits them
- require Worker reports after each completed step
- route approval-required Worker requests through the Orchestrator

## Receipt requirements

Every completed, failed, cancelled, or denied action should emit a sanitized receipt with:

- action ID
- session ID when available
- delegation ID when available
- agent role when available
- action type
- risk class
- status
- timestamp
- provider/tool reference when available
- short summary
- redaction list

Receipts must not store raw secrets, tokens, cookies, private keys, OAuth material, account identifiers, browser session data, or full private prompts.

## Done definition

The adapter contract is implemented when Buddy-Agent can:

1. Validate a BuddyAgentSession v1 payload.
2. Validate a BuddyAction v1 payload.
3. Validate a BuddyWorkerReport payload.
4. Classify the action using public-alpha risk policy.
5. Allow the Worker to continue safe read-only/draft-only steps without human interruption.
6. Require Worker reports after each completed step.
7. Pause the Worker and route approval-required actions through the Orchestrator.
8. Deny unknown, credential, money, identity, or destructive actions by default.
9. Produce a sanitized receipt for dry-run and local draft actions.
10. Expose no live account automation unless a future audited adapter explicitly enables it.
