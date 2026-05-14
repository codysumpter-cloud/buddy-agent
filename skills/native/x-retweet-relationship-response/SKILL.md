---
name: x-retweet-relationship-response
description: Use when monitoring Prismtek X posts for reposts/retweets and turning them into relationship-building actions: classify retweeters, optionally like once, draft personalized thank-you replies, queue outreach, and write KnowledgeVault receipts with strict anti-spam/rate-limit boundaries.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [x, twitter, retweets, reposts, relationship-building, devrel, content-growth, receipts]
    related_skills: [x-trend-devrel-intelligence, content-growth-social-ops, signed-in-safari-social-automation]
  buddy:
    risk_class: external-action
    auto_executable: false
    requires_explicit_approval: true
---
# X Retweet Relationship Response

## Overview

This skill monitors Prismtek X posts for reposts/retweets and turns those signals into thoughtful relationship-building. It helps Prismtek thank supporters, identify aligned builders, draft useful replies, and create KnowledgeVault relationship notes.

This is not a spam bot. It must not mass-reply, mass-like, mass-DM, or post repetitive promotional copy. It should prioritize quality, personalization, and account safety.

## Primary Use Case

When a Prismtek post gets reposted/retweeted:

1. Detect the repost event.
2. Identify the retweeter/reposter.
3. Inspect only public profile/post context.
4. Classify the retweeter:
   - builder/developer;
   - AI/tools creator;
   - creator/community account;
   - customer/prospect;
   - unknown/low-context;
   - suspicious/spam.
5. Decide the safest response path.
6. Write a KnowledgeVault relationship receipt.
7. Queue a thank-you reply or outreach draft when appropriate.
8. Require explicit approval before replies, DMs, quote posts, follows, or mentions unless the user has configured a narrow allowlist.

## Default Automation Policy

Allowed automatically after the user enables this skill for a specific X account:

- read repost/retweet events;
- deduplicate retweeters;
- create KnowledgeVault relationship notes;
- create post/reply/DM drafts;
- classify risk level;
- optionally like the retweeter's repost once if configured and rate limits are healthy.

Requires explicit approval by default:

- reply to the retweeter;
- quote post;
- tag/mention the retweeter;
- DM;
- follow;
- repost their content;
- publish any promotional call-to-action.

Blocked:

- duplicate replies to the same retweeter/post pair;
- identical generic replies under every repost;
- automated DMs;
- mass following;
- mass liking;
- aggressive retries after route/auth/platform friction;
- outreach to suspicious/spam accounts;
- fake personalization;
- claiming partnership, endorsement, or friendship that does not exist.

## Recommended Response Ladder

Use the lowest-risk useful response.

### Level 0 — Receipt Only

Use when the account is unknown, low-context, suspicious, or high-risk.

Actions:

- write receipt;
- do not engage;
- optionally add to watchlist.

### Level 1 — Like Only

Use when the retweeter appears legitimate but no strong relationship signal exists.

Actions:

- like once if user has enabled auto-like;
- write receipt;
- no reply.

### Level 2 — Thank-You Reply Draft

Use when the retweeter is relevant to Prismtek.

Actions:

- draft a personalized reply;
- queue for approval;
- do not publish automatically by default.

### Level 3 — Relationship Outreach Draft

Use when the retweeter is a strong builder/community fit.

Actions:

- create relationship note;
- draft public reply;
- draft optional DM;
- queue for explicit approval.

## Reply Style

Replies must be short, human, and specific.

Good patterns:

```txt
Appreciate the repost — building this in public so the receipts stay visible.
```

```txt
Thanks for sharing this. Prismtek is focused on the memory + execution layer for useful agents.
```

```txt
Appreciate you boosting this. If local-first agents / durable memory are your lane too, I’d be glad to compare notes.
```

Avoid repetitive generic CTA spam like:

```txt
Thanks for the repost! DM me if you want to work together!
```

Use a DM/work-together CTA sparingly and only when context supports it.

## Outreach Draft Template

```txt
Retweet Relationship Candidate
- Source post:
- Retweeter handle:
- Public profile summary:
- Why they may matter:
- Risk level:
- Suggested response level:
- Draft public reply:
- Optional DM draft:
- Approval required: yes
```

## Rate Limits and Safety Caps

Recommended defaults:

- max auto-likes per day: 10;
- max queued reply drafts per day: 10;
- max approved published replies per day: 3;
- max DMs per day: 0 by default;
- minimum delay between engagement actions: 20 minutes;
- never retry failed engagement routes more than once;
- stop immediately on auth, friction, suspicious-activity, or platform-limit errors.

## KnowledgeVault Targets

```txt
KnowledgeVault/50 - Content/x-relationship-receipts/
KnowledgeVault/50 - Content/outreach-drafts/
KnowledgeVault/50 - Content/post-ideas/
KnowledgeVault/99-System/Cron Jobs/Runs/
KnowledgeVault/99-System/Cron Jobs/Learnings/
KnowledgeVault/99-System/Cron Jobs/Next Plans/
```

## Receipt Format

```txt
Retweet Response Receipt
- Timestamp:
- Source post URL:
- Retweeter handle:
- Retweeter classification:
- Repost detected: yes/no
- Duplicate check: pass/fail
- Action taken:
- Draft created:
- Published action: yes/no
- Approval phrase used:
- Route used:
- KnowledgeVault paths:
- Uncertainty:
```

## Approval Phrases

```txt
GO X LIKE RETWEET <receipt-id>
GO X REPLY RETWEET <receipt-id>
GO X DM RETWEETER <receipt-id>
```

## Verification Checklist

- Retweeter is not suspicious/spam.
- Duplicate check passed.
- Text is not generic spam.
- CTA is context-appropriate.
- Rate limits are healthy.
- Exact text and hash are shown before publish.
- User approval exists for replies/DMs/mentions/follows.
- Receipt path is ready.
