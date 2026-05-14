---
name: market-sports-trend-intelligence
description: Use when monitoring public stock-market, crypto-market, macro, sports betting, and prediction-market discourse from X, YouTube, public data, and approved sources to create educational risk briefs, watchlists, content drafts, and manual-review decision packets without executing trades or bets.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [markets, stocks, sports, betting, x, youtube, trend-intelligence, watchlists, risk-education, content-strategy]
    related_skills: [x-trend-devrel-intelligence, sportsbook-risk-education, prediction-market-risk-education, sports-model-risk-evaluator, content-growth-social-ops]
  buddy:
    risk_class: money
    auto_executable: false
    requires_explicit_approval: true
---
# Market and Sports Trend Intelligence

## Overview

This skill helps Buddy/Hermes monitor public market and sports-betting discourse, identify narratives, track stock/sector/macro/sports signals, create educational risk briefs, build watchlists, and turn timely themes into Prismtek-native content ideas.

It is a research, education, and content-intelligence skill. It must not place trades, place bets, deposit funds, withdraw funds, sign wallet transactions, open brokerage/sportsbook accounts, route orders, chase losses, or claim guaranteed returns.

## When to Use

Use this skill when Prismtek wants to watch current stock-market trends, AI-stock narratives, sector rotations, earnings themes, macro catalysts, crypto narratives, retail-investor chatter, sports betting trends, line movement discourse, public betting narratives, injury/news uncertainty, and model-risk topics.

It can create educational analysis, risk notes, watchlists, content drafts, and manual-review decision packets.

Do not use this skill to automate trading, automate betting, provide guarantees, pressure action, or bypass platform, broker, sportsbook, wallet, or jurisdiction controls.

## Approved Sources

Approved read sources may include public X/Twitter search results, public YouTube videos/transcripts, official company investor relations pages, SEC/EDGAR filings, earnings releases, exchange notices, official league/team injury reports, schedules, box scores, reputable market data, odds data, price charts, macro calendars, KnowledgeVault notes, prior receipts, and approved user-provided research.

Do not scrape private groups, paid communities, closed Discords, private DMs, paywalled material, or account data without explicit user approval and legal access.

## Workflow

1. Define the research window, source list, and target domains: stocks, macro, crypto, sports, betting, or content opportunities.
2. Gather public signals from X, YouTube, official sources, and approved data feeds.
3. Classify signals as market narrative, catalyst, earnings/event risk, sentiment spike, sports news/injury uncertainty, line-movement narrative, model-risk theme, content opportunity, or skill/tool idea.
4. Separate facts, source claims, market chatter, and inference.
5. Produce educational briefs and watchlists with uncertainty and downside risk clearly labeled.
6. Create content drafts for X/YouTube using Prismtek's operator-infrastructure framing.
7. If the user asks about a possible stock purchase or bet, produce a manual-review decision packet rather than executing.
8. Require explicit user approval for any public post, outreach action, or regulated financial/sportsbook action.
9. Write a KnowledgeVault digest and receipt.

## Manual-Review Decision Packet

When the user asks for trade or bet help, output:

```txt
Decision Packet
- Asset / event / market:
- User thesis:
- Source facts:
- Chatter / sentiment:
- Key catalysts:
- Key risks:
- Missing information:
- Time horizon:
- Position sizing considerations:
- No-action case:
- Educational analysis:
- Content angle:
- Manual action required: yes
- Agent execution allowed: no
```

## Content Outputs

For every run, suggest:

```txt
Content Opportunities
- 5 X post drafts
- 2 X thread outlines
- 3 YouTube Short hooks
- 1 long-form YouTube outline
- 3 KnowledgeVault notes to create
- 3 trend follow-ups to monitor
```

Content must avoid guaranteed profit language, financial advice claims, "lock," "free money," or "can't lose" betting language, fake results, copied influencer posts, undisclosed sponsorship/promotion, and claims that Prismtek placed trades or bets unless a user-provided receipt verifies the user took that action manually.

## Approval and Execution Rules

Allowed without approval:

- read public sources;
- summarize public market/sports discourse;
- create watchlists;
- explain odds, volatility, implied probability, and risk concepts;
- draft content;
- draft manual-review decision packets;
- create KnowledgeVault notes.

Requires explicit approval:

- publishing X/YouTube content;
- tagging/mentioning accounts;
- replying, quoting, reposting, liking, following, or DMing;
- joining external communities;
- opening brokerage/sportsbook/wallet pages;
- preparing any broker/sportsbook/wallet action for manual review.

Blocked:

- placing stock, options, crypto, prediction-market, or sportsbook orders;
- depositing, withdrawing, transferring, or signing transactions;
- bypassing jurisdiction, broker, sportsbook, exchange, or platform controls;
- pretending to be a licensed financial advisor;
- promising returns;
- encouraging loss chasing;
- using private account data without approval;
- hammering rate-limited or blocked routes.

## KnowledgeVault Targets

Default write targets:

```txt
KnowledgeVault/50 - Content/market-sports-digests/
KnowledgeVault/50 - Content/market-watchlists/
KnowledgeVault/50 - Content/sports-risk-briefs/
KnowledgeVault/50 - Content/post-ideas/
KnowledgeVault/50 - Content/youtube-production/
KnowledgeVault/99-System/Agent Skills/candidates/
```

Never write raw credentials, brokerage tokens, sportsbook credentials, wallet keys, private DMs, or non-public personal data into KnowledgeVault.

## Verification Checklist

- Sources and time window are listed.
- Facts, claims, and inference are separated.
- Risk and no-action cases are included.
- No trade or bet execution is attempted.
- Watchlists are labeled as watchlists, not recommendations.
- Content drafts avoid guaranteed-profit language.
- KnowledgeVault paths are sanitized.
- Any external action requires explicit approval and a receipt.
