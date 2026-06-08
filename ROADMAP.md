# Buddy-Agent Roadmap

Buddy-Agent is a runnable alpha, not a finished autonomous production operator. The roadmap separates what exists now from integrations that still require design, audits, and public-safe documentation.

## Current public alpha

- Local CLI runtime with doctor, smoke, alpha, chat, memory, built-in demo skills, parity checks, and Buddy template validation.
- Safe provider abstraction with offline local fallback.
- Public skill manifests under `skills/public`.
- Conservative risk policy for skill execution.
- Local receipt primitives with sanitization.
- Governance, safety, CLI, and release checklist documentation.

## Next: public skill registry

- Expand manifest validation and registry discovery.
- Add clearer skill lifecycle docs.
- Add review metadata for public, experimental, and private skill paths.
- Keep destructive, credential, money, and identity-risk skills denied or outside public defaults.

## Next: KnowledgeVault adapter

- Add a read-only adapter contract for KnowledgeVault search.
- Keep the public default as a placeholder until audited.
- Require explicit user approval before external reads.
- Avoid storing private document contents in receipts.

## Next: Buddy-Brain bridge

- Define the narrow bridge contract for context handoff.
- Add local test doubles first.
- Document what state can cross the boundary.
- Add redaction and receipt coverage before enabling non-local bridges.

## Next: Omni bridge

- Keep Omni as an abstract/local bridge in public alpha.
- Add network enablement only behind explicit configuration and approval.
- Document fallback behavior and offline guarantees.

## Future adapters

Future adapters may include app bridges, repo tools, browser-adjacent workflows, social drafts, and other ecosystem surfaces. They must ship as audited, explicit, opt-in adapters rather than public/default live-account automation.

Out of scope for public alpha defaults: signed-in Safari automation, live X posting, credential inventory, wallet signing, deposits, withdrawals, gambling, trading, prediction-market execution, and other money/regulatory execution skills.
