# Buddy Action Adapter Contract

Buddy-Agent is the guarded execution boundary for Buddy actions from Prismtek apps. This contract defines how the app-side `BuddyAction` loop should land in the runtime without turning the public alpha into an unsupervised browser bot or live-account automation layer.

Status: design contract for public alpha. This document does not enable network actions by itself.

## Goal

Accept typed Buddy action drafts from trusted Prismtek surfaces, classify risk, require approval where needed, and return sanitized receipts.

```text
Prismtek App
  -> BuddyAction v1
  -> Buddy-Agent validation
  -> risk policy
  -> provider / skill / adapter dispatch
  -> sanitized BuddyReceipt
```

## Schema version

Buddy-Agent should accept action payloads that declare:

```text
schemaVersion = 2026-06-02.buddy-action.v1
```

The matching app-side contract currently lives in `prismtek-apps` as:

```text
vendor/buddy-core-contracts/src/actions/BuddyActionLoop.ts
```

A future canonical package can replace the vendored snapshot once package auth and release flow are stable.

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

## Future CLI shape

The public-safe CLI shape can be added later as a reviewable surface:

```bash
buddy actions validate ./action.json
buddy actions submit ./action.json --dry-run
buddy actions receipts --latest
```

Initial implementation should prefer `--dry-run` and local receipt output over real adapter execution.

## Future local API shape

A local-only API may eventually expose:

```text
POST /buddy/actions
GET /buddy/actions/:id
GET /buddy/receipts
```

Requirements before enabling any local API:

- bind to localhost by default
- require explicit opt-in
- reject unknown schema versions
- validate action risk before dispatch
- redact receipt content
- include provider and adapter IDs in receipts
- disable write/external/repo actions unless approval mode permits them

## Receipt requirements

Every completed, failed, cancelled, or denied action should emit a sanitized receipt with:

- action ID
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

1. Validate a BuddyAction v1 payload.
2. Classify the action using public-alpha risk policy.
3. Deny unknown, credential, money, identity, or destructive actions by default.
4. Produce a sanitized receipt for dry-run and local draft actions.
5. Expose no live account automation unless a future audited adapter explicitly enables it.
