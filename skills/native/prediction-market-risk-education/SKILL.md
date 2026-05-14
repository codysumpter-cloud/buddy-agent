---
name: prediction-market-risk-education
description: Use when providing responsible, non-executing education about prediction-market uncertainty, resolution rules, liquidity, source quality, and reasons to take no action.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [prediction-markets, risk-education, resolution-rules, no-execution]
    related_skills: [sportsbook-risk-education, sports-model-risk-evaluator]
  buddy:
    risk_class: money
    auto_executable: false
    requires_explicit_approval: true
---
# Prediction Market Risk Education

## Overview

This skill helps Hermes and Buddy discuss prediction-market style questions in a non-executing way. It focuses on uncertainty, resolution-rule reading, source quality, liquidity awareness, and no-action reasoning.

It must not route orders, sign wallets, custody assets, transfer funds, use exchange credentials, or present financial activity as automated.

## When to Use

Use this skill when the user wants help reading market wording, comparing evidence quality, identifying ambiguous settlement criteria, or understanding why taking no action may be safer.

## Workflow

1. Restate the question and resolution criteria.
2. Identify ambiguous language, missing evidence, and timing risks.
3. Review source credibility and uncertainty.
4. Produce an educational risk brief with no-action reasons.
5. Keep all financial decisions outside the agent.

## Common Pitfalls

- Do not imply certainty from market price alone.
- Do not ignore ambiguous resolution rules.
- Do not provide wallet, custody, or execution instructions.
- Do not pressure the user to act.

## Verification Checklist

- The output is educational and non-executing.
- Resolution ambiguity is surfaced.
- No wallet, credential, or fund movement step appears.
- No guarantee or pressure language appears.
