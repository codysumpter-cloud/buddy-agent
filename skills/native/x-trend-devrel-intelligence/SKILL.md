---
name: x-trend-devrel-intelligence
description: Use when monitoring public X/Twitter trends, AI development stacks, developer conversations, and ecosystem signals to create KnowledgeVault digests, post drafts, and approval-gated relationship-building outreach.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [x, twitter, trends, devrel, ai-stacks, knowledge-vault, content-strategy, outreach-drafts]
    related_skills: [hermes-x-insights-analyst, content-growth-social-ops, signed-in-safari-social-automation]
  buddy:
    risk_class: external-action
    auto_executable: false
    requires_explicit_approval: true
---
# X Trend DevRel Intelligence

## Overview

This skill helps Buddy/Hermes monitor public X/Twitter discourse, AI development stacks, developer conversations, repo launches, tool announcements, and builder communities. It turns those signals into KnowledgeVault notes, post ideas, relationship maps, and approval-gated outreach drafts.

This is not a spam, scraping, or mass-DM skill. It must not automatically follow, like, repost, reply, DM, tag, mention, or contact people. It drafts and queues relationship-building actions for explicit approval.

## When to Use

Use this skill when Prismtek wants to find trending AI/developer topics, identify useful builders and communities, map AI stacks, draft timely posts, draft thoughtful outreach, and update KnowledgeVault with trends, repos, people, skills, and content opportunities.

Do not use this skill to mass-message, scrape private data, impersonate, astroturf, manipulate engagement, or bypass platform limits.

## Workflow

1. Define the research window, target themes, and approved sources.
2. Search or inspect public signals for AI/dev-stack trends and builder conversations.
3. Extract trends, accounts, repos, stacks, claims, links, and open questions.
4. Classify each signal as trend, content opportunity, person to follow manually, possible collaborator, repo/tool to research, skill idea, or KnowledgeVault update.
5. Create a KnowledgeVault trend digest with source links where available.
6. Draft X posts, threads, or replies as queue candidates with exact text and intended audience.
7. Draft outreach messages only as manual-review candidates.
8. Require explicit approval before any external action.
9. After approved public actions, write a receipt with timestamp, route, URL, and uncertainty.

## Outreach Rules

Allowed without approval:

- identify public accounts or repos;
- summarize public posts;
- draft replies or DMs;
- suggest people to follow;
- create a relationship map;
- create KnowledgeVault notes.

Requires explicit approval:

- follow;
- like;
- repost;
- reply;
- quote post;
- DM;
- tag or mention a person;
- subscribe;
- join a Discord/Slack/community;
- open a pull request or issue;
- send email;
- publish any post.

Blocked:

- spam or mass outreach;
- fake personalization;
- scraping private or non-public data;
- exporting cookies or sessions;
- bypassing X limits or anti-abuse systems;
- harassment or dogpiling;
- undisclosed paid promotion;
- pretending Prismtek has a relationship that does not exist.

## KnowledgeVault Updates

Default write targets:

```txt
KnowledgeVault/50 - Content/trend-digests/
KnowledgeVault/50 - Content/outreach-drafts/
KnowledgeVault/50 - Content/post-ideas/
KnowledgeVault/99-System/Agent Skills/candidates/
```

Never write raw credentials, cookies, tokens, private DMs, private emails, or unapproved personal data into KnowledgeVault.

## Common Pitfalls

- Do not mistake trending for strategically useful.
- Do not copy viral posts; extract structure and make Prismtek-native commentary.
- Do not imply friendship, endorsement, or partnership from public engagement.
- Do not overfit content to every trend; Prismtek's lane is durable memory, guarded execution, local-first agents, dev tools, and receipts.
- Do not publish based on unverified claims without labeling uncertainty.

## Verification Checklist

- Sources are approved and public or user-provided.
- Trend digest separates facts from inferences.
- Outreach is draft-only unless approved.
- No mass outreach is proposed.
- No private data or secrets are stored.
- X posts are queued with exact text/hash when publishing is requested.
- KnowledgeVault paths are sanitized.
- Any external action has a receipt requirement.
