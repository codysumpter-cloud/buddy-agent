---
name: hermes-precall-context-brief
description: Use when preparing concise pre-call context briefs from approved notes, prior conversations, public signals, project status, and open questions.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [pre-call, meetings, briefing, context, productivity]
    related_skills: [hermes-reflect-memory-analyst, hermes-bookmark-research-digest]
  buddy:
    risk_class: read-only
    auto_executable: true
    requires_explicit_approval: false
---
# Hermes Pre-call Context Brief

## Overview

This skill prepares concise context briefs before calls, meetings, interviews, streams, collaborations, or stakeholder conversations. It uses only approved notes, prior context, public signals, and project status.

It must not access private calendars, emails, social accounts, recordings, or documents unless the user has explicitly approved the source.

## When to Use

Use this skill when the user wants a fast pre-call summary, relationship context, current project state, talking points, risks, and open questions.

## Workflow

1. Identify the person, meeting purpose, timeframe, and approved sources.
2. Summarize relationship context, known goals, open loops, and recent changes.
3. Generate talking points, questions, and likely risks.
4. Flag missing context instead of inventing details.
5. Produce a concise brief the user can scan quickly.

## Common Pitfalls

- Do not invent private details.
- Do not over-share sensitive context.
- Do not read unapproved sources.
- Do not treat stale project notes as current without warning.

## Verification Checklist

- Source boundaries are clear.
- Sensitive details are minimized.
- Open questions are explicit.
- Brief is concise and actionable.
