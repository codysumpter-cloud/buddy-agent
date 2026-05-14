---
name: hermes-reflect-memory-analyst
description: Use when synthesizing approved memory, notes, sessions, and KnowledgeVault context into patterns, top insights, decision support, and next actions.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, reflection, knowledge-vault, insights, productivity]
    related_skills: [hermes-bookmark-research-digest, hermes-precall-context-brief]
  buddy:
    risk_class: read-only
    auto_executable: true
    requires_explicit_approval: false
---
# Hermes Reflect Memory Analyst

## Overview

This skill synthesizes approved memory, notes, prior sessions, and KnowledgeVault context into patterns, insights, decisions, and next actions.

It must not delete memory, overwrite canonical notes, export private memory externally, or store secrets.

## When to Use

Use this skill for weekly reviews, context reconstruction, project continuity, decision summaries, personal operating-system notes, and KnowledgeVault synthesis.

## Workflow

1. Identify the approved memory or note scope.
2. Extract recurring themes, constraints, decisions, open loops, and contradictions.
3. Produce concise insights with confidence levels.
4. Suggest next actions without mutating memory.
5. Mark any needed memory write as approval-required.

## Common Pitfalls

- Do not treat stale memory as current fact.
- Do not erase or rewrite memory without approval.
- Do not expose sensitive personal data unnecessarily.
- Do not invent prior context.

## Verification Checklist

- Source scope is explicit.
- Insights distinguish fact from inference.
- No memory deletion occurs.
- Any write/update is approval-gated.
