# Buddy Feature Parity

This document tracks the intended feature surface for Buddy Agent across iOS, Windows, Buddy Brain, Omni Buddy, Prismtek Apps, and Knowledge Vault.

The machine-checkable source of truth is `src/buddy_agent/parity.py`. Run `buddy parity` or `buddy doctor` before claiming parity is intact.

## Current parity status

| Surface | Owner | Buddy Agent boundary | Status |
| --- | --- | --- | --- |
| iOS app | `codysumpter-cloud/prismtek-apps` | Phone-native Buddy UX, app-container state, mobile model packaging | Contracted; mobile runtime still needs on-device validation |
| Windows app | `codysumpter-cloud/prismtek-apps` | Localhost desktop shell and Gemma 4 gateway | Contracted; gateway must be checked on Windows |
| Buddy Brain | `codysumpter-cloud/buddy-brain` | Operator context, council policy, runbooks, Codex bridge | Contracted; external repo doctors remain authoritative |
| Omni Buddy | `codysumpter-cloud/omni-buddy` | Offline voice, vision, transport, and local routing | Contracted; hardware/runtime checks remain external |
| Knowledge Vault | `codysumpter-cloud/knowledge-vault` | Source map, public repo steward, provenance, private boundary | Contracted; vault path and generated markers remain external |

## iOS app parity

Buddy Agent must preserve these capabilities for the iBeMore / BeMore iOS shell:

- `buddy.identity` — identity, archetype, class, role, palette, and voice selections.
- `buddy.progression` — level, XP, bond, evolution tier, anti-grind, and proficiency state.
- `buddy.appearance-profile` — ASCII, pixel, customization, profile, and render-state metadata.
- `buddy.runtime-events` — idempotent runtime events with actor, payload, effects, and receipts.
- `buddy.trade-package` — trade-ready Buddy snapshots with provenance metadata.
- `llm.phone-native-runtime` — phone inference must use mobile-ready runtime artifacts, not raw desktop `.gguf` assumptions.

Validation owner: `codysumpter-cloud/prismtek-apps`.

Expected validation:

```bash
# From prismtek-apps, using the iOS test/build path available on the machine.
# Run BuddyContracts, BuddyRuntimeTests, and BuddyAppearanceStudioTests.
```

## Windows app parity

Buddy Agent must preserve these capabilities for the Windows shell:

- `gemma4.desktop-gateway` — Gemma 4 routes through an OpenAI-compatible local endpoint.
- `gemma4.status-endpoint` — gateway exposes `GET /api/gemma4/status`.
- `gemma4.chat-endpoint` — gateway exposes `POST /api/gemma4/chat`.
- `gemma4.openapi-action` — gateway exposes OpenAPI files for optional custom GPT Action wiring.

Validation owner: `codysumpter-cloud/prismtek-apps`.

Expected validation:

```powershell
.\scripts\start-bemore-buddy-windows.ps1
Invoke-RestMethod http://127.0.0.1:4320/api/gemma4/status
```

The Windows gateway is not proof that iOS local inference works. Phone-native inference still needs LiteRT, MediaPipe, AI Edge, or MLC-ready mobile package validation.

## Buddy Brain parity

Buddy Agent must preserve these capabilities for Buddy Brain:

- `operator.startup-context` — startup context comes from core operator files.
- `council.contracts` — council roles and operating policy stay in Buddy Brain.
- `workspace.sync` — workspace sync and operator reports use adapter boundaries.
- `codex.bridge` — Codex dispatch stays isolated through bridge artifacts.

Validation owner: `codysumpter-cloud/buddy-brain`.

Expected validation:

```bash
make doctor
make runtime-doctor
make workspace-sync
make project-snapshot
```

## Omni Buddy parity

Buddy Agent must preserve these capabilities for Omni Buddy:

- `omni.local-routing` — local LLM routing supports Omni first with Ollama fallback.
- `omni.voice-loop` — wake, listen, thinking, speaking, and error states are adapter-owned.
- `omni.vision-loop` — vision captioning can remain local or hybrid.
- `omni.transport-policy` — online, mesh, Reticulum fallback, and auto modes stay explicit.

Validation owner: `codysumpter-cloud/omni-buddy`.

Expected validation:

```bash
./scripts/bmo_omni_doctor.sh
./scripts/run_validation_matrix.sh
```

## Knowledge Vault parity

Buddy Agent must preserve these capabilities for Knowledge Vault:

- `vault.source-map` — vault map defines inbox, projects, runbooks, and system areas.
- `vault.public-repo-steward` — Vault Steward tracks public repo metadata.
- `vault.provenance` — retrieved sources keep path, title, source id, and metadata.
- `vault.private-boundary` — automation must not read or write private credential notes.

Validation owner: `codysumpter-cloud/knowledge-vault`.

Expected validation:

```bash
# Confirm 99-System/Vault Map.md and Vault Steward generated markers before syncing.
# Confirm 00-Private/Credentials remains excluded from Git automation.
```

## Runtime parity from Hermes Agent

These are still scoped as future runtime work, not parity complete:

- [ ] Terminal chat runtime
- [ ] Model provider selection
- [ ] Tool registry and toolsets
- [ ] Persistent memory
- [ ] Skill creation and skill execution
- [ ] Scheduled automations
- [ ] Messaging gateway
- [ ] Sandboxed command execution
- [ ] Subagents and delegated workstreams
- [ ] Browser/web tooling

## Definition of done

A feature is not complete until it has:

1. A documented owner and boundary.
2. Tests or validation commands.
3. Security and secret-handling notes where relevant.
4. Source provenance recorded when adapted from another repo.
5. A passing `buddy parity` and `buddy doctor` result in Buddy Agent.
