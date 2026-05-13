---
name: hermes-bookmark-research-digest
description: Use when turning approved bookmarks and linked articles into ranked research digests, summaries, and next actions using read-only browser or API adapters.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bookmarks, research, digest, browser-readonly, knowledge-vault]
    related_skills: [hermes-x-insights-analyst, hermes-reflect-memory-analyst]
  buddy:
    risk_class: external-action
    auto_executable: false
    requires_explicit_approval: true
---
# Hermes Bookmark Research Digest

## Overview

This skill converts approved bookmarks, reading lists, public URLs, and exported notes into ranked research digests. It is read-first and source-grounded.

Browser or API access must be read-only. It must not log in, submit forms, change bookmarks, purchase content, or store credentials.

## When to Use

Use this skill for research catch-up, saved-link triage, article clustering, source summaries, or extracting follow-up actions from a reading queue.

## Workflow

1. Confirm the approved bookmark set or URL list.
2. Fetch or read each source through an approved read-only adapter.
3. Summarize claims, evidence, novelty, and relevance.
4. Rank items by usefulness, urgency, and confidence.
5. Produce next actions and KnowledgeVault-ready notes.

## Common Pitfalls

- Do not summarize inaccessible private content as if it was read.
- Do not use write-capable browser automation.
- Do not collapse conflicting sources into one certainty.
- Do not store private tokens or cookies.

## Verification Checklist

- Every summarized source was available and approved.
- Read-only access was used.
- Claims and uncertainty are separated.
- Follow-up actions are drafts, not executed actions.
