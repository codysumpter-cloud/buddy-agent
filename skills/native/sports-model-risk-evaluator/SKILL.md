---
name: sports-model-risk-evaluator
description: Use when reviewing sports prediction data pipelines, backtests, calibration, leakage, uncertainty, and model-risk controls without regulated execution.
version: 1.0.0
author: Prismtek / Buddy-Hermes Skill Bridge
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [machine-learning, sports-models, backtesting, calibration, risk]
    related_skills: [sportsbook-risk-education, prediction-market-risk-education]
  buddy:
    risk_class: money
    auto_executable: false
    requires_explicit_approval: true
---
# Sports Model Risk Evaluator

## Overview

This skill helps Hermes and Buddy review sports-prediction model pipelines in a responsible, non-executing way. It focuses on data quality, leakage, backtest validity, calibration, uncertainty, and explainability.

It must not automate regulated activity or present model output as guaranteed.

## When to Use

Use this skill when evaluating a sports-model dataset, feature set, forecast, backtest, confidence score, or API design.

## Workflow

1. Identify the model target, data sources, features, and validation period.
2. Check for leakage, survivorship bias, stale data, and missing context.
3. Review calibration, error bars, sample size, and out-of-sample performance.
4. Produce a model-risk brief and recommended non-executing improvements.

## Common Pitfalls

- Do not overfit to historic results.
- Do not confuse accuracy with profitable or safe decisions.
- Do not ignore uncertainty intervals.
- Do not hide model limitations.

## Verification Checklist

- Data risks are named.
- Evaluation method is clear.
- Output remains non-executing.
- No guarantee or money-action instruction appears.
