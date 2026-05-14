# Buddy-Agent Safety Model

Buddy-Agent is the guarded execution layer for Prismtek's Agentic OS. It connects runtime shell, skills, memory, policies, adapters, and receipts while keeping the public alpha safe-by-default.

## Core posture

Buddy-Agent is alpha software. The public alpha should be honestly runnable, inspectable, and useful for local guarded experiments. It should not claim to be a finished autonomous production agent.

## Default runtime boundary

Public defaults are local and manual:

```bash
BUDDY_PROVIDER=local
BUDDY_NETWORK_ENABLED=false
BUDDY_APPROVAL_MODE=manual
BUDDY_SKILLS_PATH=skills/public
```

The default provider is `LocalEchoProvider`, which does not use the network. Unknown providers fall back to local when network execution is disabled.

## Approval model

Skill manifests declare risk metadata. The default policy allows read-only and draft-only skills, sends write/external/repo mutation skills to review, and denies credential, money, destructive, and identity-risk skills by default.

## Receipts

Receipts are local summaries, not raw transcripts. They should record action, status, summary, safe metadata, and timestamp. They must not store secrets, cookies, tokens, passwords, account identifiers, private keys, OAuth material, browser session data, or private prompts.

## Public default exclusions

The public/default runtime must not include:

- signed-in Safari automation;
- browser session automation;
- live social posting;
- credential inventory;
- gambling, trading, prediction-market execution;
- wallet signing;
- deposits or withdrawals;
- money-action instructions;
- unaudited private Hermes environment paths.

## Adapter strategy

Public alpha adapters should be contracts, placeholders, or local test doubles unless audited. When unsure, document the integration as future work instead of pretending it works.

## Documentation honesty

Use terms like `runnable alpha`, `guarded execution layer`, and `public-safe default`. Avoid terms that imply full autonomy, production readiness, live account control, or unsupervised operation.
