---
name: sportsbook-risk-education
description: Use when providing responsible, non-executing education about sportsbook-style risk, uncertainty, probability language, loss limits, and reasons to take no action.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [risk-education, probability, responsible-use, no-execution]
    related_skills: [bettingai-model-advisor, polymarket-risk-education]
  buddy:
    risk_class: money
    auto_executable: false
    requires_explicit_approval: true
---
# Sportsbook Risk Education

## Overview

This skill helps Hermes and Buddy explain uncertainty, probability language, loss exposure, responsible-use boundaries, and no-action reasoning for sportsbook-style discussions. It is educational only and never executes or queues financial activity.

## When to Use

Use this skill when the user wants a sober risk review, probability literacy, responsible-use checklist, or help identifying why no action may be the safest option.

Do not use it to place, route, automate, optimize, or encourage gambling activity.

## Workflow

1. Restate the uncertainty and the user-provided assumptions.
2. Explain what information is missing or unreliable.
3. Identify downside, emotional decision risks, and loss-limit considerations.
4. Present non-executing educational notes and no-action reasons.
5. Require the user to make any regulated decision outside the agent.

## Common Pitfalls

- Do not imply guaranteed outcomes.
- Do not pressure action.
- Do not encourage loss chasing.
- Do not access accounts or funds.

## Verification Checklist

- Output is educational.
- No execution path is provided.
- No profit guarantee appears.
- No account, credential, or payment action is requested.
