---
name: governed-market-intelligence-loop
description: Use when running or improving a market intelligence loop that observes stocks, macro, filings, social sentiment, analyst/fundamental changes, congressional disclosures, and account risk state to produce evidence-backed proposals without executing trades.
version: 1.0.0
author: Prismtek / Hermes Skill Bridge
license: MIT
platforms: [macos, linux, windows, vps]
metadata:
  hermes:
    tags: [markets, stocks, risk, intelligence-loop, proposal-only, model-agnostic, provider-agnostic, cron, tradingagents, investskill]
    related_skills: [market-sports-trend-intelligence, polymarket-trading-advisor, sportsbook-betting-advisor]
  buddy:
    risk_class: money
    auto_executable: false
    requires_explicit_approval: true
---
# Governed Market Intelligence Loop

## Overview

This skill turns a market cron idea into a governed intelligence system. It is designed for Buddy/Hermes to monitor watchlists, positions, filings, congressional disclosures, social/X sentiment, analyst/fundamental changes, market price/volume behavior, and stored investment theses across any model/provider stack.

The skill is **proposal-only**. It must not place trades, modify orders, resize exposure, change stops, deposit, withdraw, or open broker/wallet/sportsbook actions unless a separate explicit user approval and broker-specific execution skill/policy exists.

The target architecture is:

```txt
Observe -> Validate -> Score -> Propose -> Require Approval -> Log
```

Cron is only a heartbeat. The application decides whether a run is valid.

## Provider-Agnostic Roles

Any model/provider can be used if it is forced through schemas and risk policy:

- `collector`
- `normalizer`
- `bull_analyst`
- `bear_analyst`
- `risk_reviewer`
- `synthesizer`
- `auditor`

Provider rules:

- Every model output must be coerced into schemas.
- A model cannot bypass risk policy.
- A model cannot authorize execution.
- A model cannot mark unsupported claims high confidence.
- Deterministic policy has veto power over all model agents.

## Allowed Actions

Allowed:

- load canonical state;
- read account/position/order state through read-only adapters;
- read market data through approved adapters;
- read filings, disclosures, public news, and social/X sentiment through approved read-only adapters;
- normalize signals;
- score divergence;
- create watch/proposal/human-review alerts;
- create daily/weekly digests;
- create KnowledgeVault notes;
- create content ideas from public market narratives;
- create proposal packets requiring approval.

Not allowed inside this skill:

- placing orders;
- cancelling/modifying orders;
- changing stops;
- increasing/decreasing exposure;
- rotating into a new ticker;
- opening broker/wallet pages for action;
- deposits/withdrawals/transfers;
- signing wallet transactions;
- presenting watchlists as direct financial recommendations.

## Required State

Every run must load:

- watchlist;
- active holdings;
- queued orders;
- original thesis per ticker;
- active risk policy;
- previous run summary;
- last alert sent per ticker;
- previous divergence scores;
- current exposure limits.

If critical state cannot be loaded, fail closed.

## Schedule Guidance

Do not use only `0 * * * *`.

Recommended Eastern Time schedule:

```cron
CRON_TZ=America/New_York
15 8 * * 1-5  hermes premarket-scan --proposal-only
25 9 * * 1-5  hermes open-risk-check --require-human-approval
7,22,37,52 9-15 * * 1-5 hermes market-loop --proposal-only
5 16 * * 1-5 hermes close-review --digest
30 17 * * 1-5 hermes slow-signal-scan --proposal-only
15 20 * * 1-5 hermes calibrate-thresholds --no-live-actions
```

Use market-calendar guards inside the app.

## Signal Schema

Every signal must become structured data:

```txt
Signal
- ticker
- source
- direction
- confidence
- severity
- freshness_minutes
- latency_class
- evidence_url
- evidence_hash
- summary
- limitations
```

No evidence URL/hash means no high-confidence alert.

## Divergence Scoring

```txt
DivergenceScore
- ticker
- price_trend_score
- sentiment_score
- fundamental_score
- insider_score
- disclosure_score
- risk_score
- total
- action: silent | watch | proposal | human_review
```

Thresholds:

```txt
< 0.35 -> silent
0.35-0.54 -> watch
0.55-0.74 -> proposal
>= 0.75 -> human_review
```

High confidence requires at least two verified independent sources and primary-source evidence.

## Alert Tiers

```txt
P0 — security issue, broken guardrail, unexpected order, exposure breach
P1 — high-confidence thesis break, human review required
P2 — material divergence, proposal generated
P3 — watchlist note, include in digest
P4 — noise, log only
```

Stable runs should be logged only unless a digest is due.

## Proposal Format

When divergence is found, output:

```md
# Risk Proposal: {TICKER}

## Alert Tier
P1 / P2 / P3

## Current Position
- Shares:
- Market value:
- Portfolio exposure:
- Unrealized P&L:

## Trigger
What changed?

## Evidence
- Source 1:
- Source 2:
- Source 3:

## Signal Classification
- Source type:
- Freshness:
- Confidence:
- Latency class:
- Primary-source verified: yes/no

## Thesis Impact
- Original thesis:
- New contradiction:
- Severity:

## Recommended Action
- Hold
- Watch
- Reduce proposed exposure
- Tighten proposed risk limit
- Pause new buys
- Human review required

## What Hermes Is Not Doing
- No automatic trade placed
- No order changed
- No stop changed
- No exposure changed

## Approval Required
Yes / No
```

## Verification Checklist

- No execution route was used.
- Model/provider outputs were schema-normalized.
- Risk policy had veto authority.
- Congressional disclosures were tagged delayed.
- No high-confidence alert came from one source.
- Run lock/idempotency was used or recommended.
- Stable runs were logged, not spammed.
- Receipts/audit logs were written.
- Any proposal clearly states approval requirements.
