---
name: signed-in-safari-social-automation
description: Use when a normal isolated browser session cannot access signed-in X, YouTube, or Google state, but the user has explicitly approved using their physical signed-in Safari session through Apple Events JavaScript.
version: 1.0.0
author: Prismtek / Hermes Operator Notes
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [safari, apple-events, social-media, x, youtube, signed-in-session, approval-gated]
    related_skills: [content-growth-social-ops, hermes-x-insights-analyst, moneyprinter-content-factory]
  buddy:
    risk_class: external-action
    auto_executable: false
    requires_explicit_approval: true
---
# Signed-in Safari Social Automation

## Overview

This skill documents the approved fallback path for social and creator-platform browser work when isolated browser sessions do not inherit the user's real login state.

Use the physical signed-in Safari session through Apple Events JavaScript only after explicit user approval. Prefer read-only verification and draft preparation. Any external account change, publishing action, or profile mutation requires a clear receipt and approval boundary.

## When to Use

Use this skill when X, YouTube Studio, Google, or similar browser workflows fail in isolated automation but are already signed in inside the user's local Safari session.

Do not use this skill for credential collection, password entry, cookie export, session hijacking, bypassing MFA, or hidden account actions.

## Working Procedure

1. Confirm the user explicitly authorizes local signed-in Safari automation for the target site and action.
2. Use Apple Events JavaScript against the active Safari tab or a clearly opened target URL.
3. Prefer DOM reads, form filling, and native browser interactions that leave visible UI state.
4. For React-controlled fields, use native setters plus `input` and `change` events so the page state updates correctly.
5. Avoid paid or rate-limited APIs when the approved signed-in Safari DOM path is enough.
6. Capture secret-free receipts: page, action, before/after UI state, visible counts, and verification limits.
7. Do not claim public visibility until a logged-out or public verification path confirms it.

## Supported Flows

- X profile update review and user-approved edits.
- X native compose flow with visible confirmation.
- YouTube Studio signed-in verification.
- Public-facing receipt generation without secrets.

## Common Pitfalls

- Isolated browser tools do not inherit Safari login state.
- System Events keystrokes require Accessibility permissions and may be blocked.
- React inputs may not update if values are assigned without native setters/events.
- UI-published does not always mean publicly indexed or visible to logged-out users.
- Duplicate skill references can cause ambiguous skill loading.

## Verification Checklist

- User approval was explicit.
- No raw secrets, cookies, passwords, or tokens were copied into notes or logs.
- File receipts avoid sensitive values.
- Public visibility is verified separately from local UI publication.
- Any account-changing step is described precisely and conservatively.
