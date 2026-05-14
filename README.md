<p align="center">
  <img src="assets/buddy-agent-mascot.svg" alt="Buddy Agent animated tama-style Buddy mascot" width="280">
</p>

<h1 align="center">Buddy Agent</h1>

<p align="center"><strong>Native Buddy runtime for the Prismtek / Hermes ecosystem.</strong></p>

<p align="center">
  <a href="https://github.com/codysumpter-cloud/buddy-agent/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/codysumpter-cloud/buddy-agent/ci.yml?branch=main&label=CI&style=for-the-badge" alt="CI"></a>
  <a href="https://github.com/codysumpter-cloud/buddy-agent/releases"><img src="https://img.shields.io/github/v/release/codysumpter-cloud/buddy-agent?include_prereleases&label=Release&style=for-the-badge" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Prismtek%20Source%20Available-blueviolet?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/codysumpter-cloud/buddy-agent/archive/refs/heads/main.zip"><img src="https://img.shields.io/badge/Download-ZIP-22c55e?style=for-the-badge" alt="Download ZIP"></a>
  <a href="https://github.com/codysumpter-cloud/buddy-agent.git"><img src="https://img.shields.io/badge/Clone-Repo-0ea5e9?style=for-the-badge" alt="Clone Repo"></a>
  <a href="https://github.com/codysumpter-cloud/buddy-agent/issues"><img src="https://img.shields.io/badge/Roadmap-Issues-f59e0b?style=for-the-badge" alt="Roadmap Issues"></a>
</p>

## Install

```bash
git clone https://github.com/codysumpter-cloud/buddy-agent.git
cd buddy-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
buddy doctor
buddy smoke
buddy alpha
```

## Alpha Runtime Plus

```bash
buddy chat "hello buddy"
buddy app-chat "hello from widget" --surface widget
buddy remember "Prismtek likes clean runtime seams"
buddy recall "runtime"
buddy skill --skill caps "buddy alpha"
```

The Alpha Runtime Plus path wires Buddy-native runtime config, backend execution, persistent memory, vault-style retrieval, Buddy Brain operator context, local Omni routing, Buddy template loading, app bridge eventing, built-in skills, and companion permission policy into one runnable local path.

This is still an alpha milestone. It is not full Hermes Agent or full ecosystem feature parity. Reference repositories are tracked and mapped, but each source capability should only be marked complete after it is ported, rebranded, wired, tested, documented, and license-audited.

## Generate a Buddy

```bash
buddy generate --output my-buddy
```

This writes an app-safe starter template with `buddy.json` and `ascii_frames.json`.

Generated Buddies must support:

- render modes: `pixel` and `ascii`
- animation states: `idle`, `happy`, `thinking`, `sleepy`
- frame contract: `64x64`, centered, equal padding

## Visual Roles

| Role | Asset |
| --- | --- |
| README animated mascot | `assets/buddy-agent-mascot.svg` |
| App icon | `assets/buddy-app-icon.svg` |
| Default Buddy appearance | `assets/default-buddy.svg` |
| Reference image manifest | `assets/references/REFERENCE_IMAGES.md` |

The app icon can be a pocket-pet device mark. The actual Buddy is the animated pet inside the app.

## Companion Direction

Buddy is being designed as a persistent companion layer for desktop, browser, widgets, and the iBeMore iOS app. See `docs/IBE_MORE_COMPANION_SPEC.md`.

## Version Tracker

| Track | Status |
| --- | --- |
| Runtime | <img src="assets/status-dot.svg" width="12" alt="online"> Alpha Runtime Plus branch |
| Package | `0.1.0` alpha scaffold |
| CLI | `buddy` |
| Smoke test | `buddy smoke` |
| Alpha path | `buddy alpha`, `chat`, `app-chat`, `remember`, `recall`, `skill`, `parity` |
| Runtime config | JSON loader with safe local defaults |
| Backend execution | callable local template backend boundary |
| Memory | persistent JSON-backed local memory |
| Retrieval | local vault-style provider backed by note index |
| Buddy Brain layer | local operator context adapter |
| Omni routing | local callable backend adapter, provider-ready seam |
| App bridge route | typed `app-chat` route and in-process event bridge |
| Appearance template | Default Buddy supports pixel and ASCII modes |
| Companion shell | loads and validates `templates/default-buddy/buddy.json` |
| iBeMore bridge | typed app bridge contracts started |
| Hermes reference | tracked reference; source parity not yet complete |
| Discovery input | `awesome-hermes-agent` |
| Compression input | `caveman` |
| Restricted experiments | Disabled by default |

## Ecosystem Scope

Buddy Agent tracks Hermes Agent, Buddy Brain, Omni Buddy, Prismtek Apps, Knowledge Vault, Awesome Hermes Agent, Caveman, and the expanded Prismtek/Hermes ecosystem. See `docs/ECOSYSTEM_INTEGRATION_MAP.md`, `docs/ECOSYSTEM_LICENSE_AUDIT.md`, and `docs/BUDDY_APPEARANCE_SPEC.md`.

## Current Status

Implemented alpha pieces:

- `buddy` CLI with status, doctor, smoke, alpha, chat, app-chat, remember, recall, skill, parity, and generate commands
- runnable local Alpha Runtime Plus composition
- runtime config loader and backend execution seam
- persistent JSON-backed local memory
- local vault-style retrieval provider
- local Buddy Brain operator context adapter
- local Omni-style routing adapter backed by the runtime backend seam
- typed app bridge chat route and local event bridge
- built-in summarize and caps skills
- app icon asset, README mascot asset, and default Buddy asset
- app-safe Buddy appearance contract for pixel/ascii modes and 64x64 animation states
- companion shell loader for the canonical default Buddy template
- companion contracts, consent-first policy, and iBeMore app bridge contracts
- runtime engine, message state, tool calls, and tool registry
- Buddy profile, care, and training domain helpers
- note index, skill registry, automation registry, sandbox policy, app bridge contracts, gateway contracts, and Omni config
- ecosystem integration registry and CI scaffolding

Still not claimed complete:

- full Hermes Agent source feature parity
- full Buddy Brain operator/council parity
- full AgentMemory or Knowledge Vault parity
- full Omni local model/voice/vision parity
- full Prismtek Apps or iBeMore app integration
- restricted experiment enablement

## Development

```bash
ruff check .
mypy src
pytest
buddy --help
buddy doctor
buddy smoke
buddy alpha
buddy app-chat "hello from app" --surface widget
buddy generate --output my-buddy
```

## Licensing

Repository-owned code uses `LICENSE` unless a file or directory states otherwise. Hermes-derived code remains governed by the original MIT license and notices. Expanded ecosystem integrations must be audited before code is copied or substantially adapted.
