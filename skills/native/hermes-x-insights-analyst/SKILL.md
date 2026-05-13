---
name: hermes-x-insights-analyst
description: Use when summarizing approved X accounts, posts, or timelines into read-only insight reports while blocking posts, replies, reposts, likes, DMs, and cookie-based write tooling.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [x, twitter, read-only, insights, daily-brief, social-media]
    related_skills: [content-growth-social-ops, hermes-bookmark-research-digest]
  buddy:
    risk_class: read-only
    auto_executable: true
    requires_explicit_approval: false
---
# Hermes X Insights Analyst

## Overview

This skill turns approved X/Twitter sources into read-only insight reports. It can summarize themes, identify recurring accounts or narratives, extract content ideas, and recommend draft-only follow-up prompts.

It must not post, reply, repost, like, DM, change settings, use cookies, or operate write-capable X tooling.

## When to Use

Use this skill for daily social signal reviews, account research, public post summaries, trend notes, and content inspiration from approved sources.

## Workflow

1. Confirm the approved accounts, links, screenshots, exports, or public sources.
2. Extract themes, questions, repeated claims, and useful hooks.
3. Separate facts from speculation.
4. Produce a concise insight report and optional draft prompts.

## Common Pitfalls

- Do not rely on private account access.
- Do not treat social chatter as verified fact.
- Do not engage from the user account.
- Do not preserve cookies or credentials.

## Verification Checklist

- Sources were approved.
- Output is read-only.
- No account actions are attempted.
- Unverified claims are labeled.
