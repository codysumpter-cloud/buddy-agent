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
  <a href="https://github.com/codysumpter-cloud/buddy-agent"><img src="https://img.shields.io/badge/Clone-Repo-0ea5e9?style=for-the-badge" alt="Clone Repo"></a>
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
```

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

The app icon can be a pocket-pet device mark. The actual Buddy is the animated pet inside the app.

## Companion Direction

Buddy is being designed as a persistent companion layer for desktop, browser, widgets, and the iBeMore iOS app. See `docs/IBE_MORE_COMPANION_SPEC.md`.

## Version Tracker

| Track | Status |
| --- | --- |
| Package | `0.1.0` scaffold |
| CLI | `buddy` |
| Appearance template | Default Buddy supports pixel and ASCII modes |
| Companion shell | Contracts and consent-first policy started |
| iBeMore bridge | Typed app bridge contracts started |
| Runtime | Native scaffold, not full Hermes port yet |
| Hermes reference | Planned import from `NousResearch/hermes-agent` |
| Discovery input | `awesome-hermes-agent` |
| Compression input | `caveman` |
| Restricted experiments | Disabled by default |

## Ecosystem Scope

Buddy Agent tracks Hermes Agent, Buddy Brain, Omni Buddy, Prismtek Apps, Knowledge Vault, Awesome Hermes Agent, Caveman, and the expanded Prismtek/Hermes ecosystem. See `docs/ECOSYSTEM_INTEGRATION_MAP.md`, `docs/ECOSYSTEM_LICENSE_AUDIT.md`, and `docs/BUDDY_APPEARANCE_SPEC.md`.

## Current Status

Implemented scaffold pieces:

- `buddy` CLI with status, doctor, and generate commands
- app icon asset, README mascot asset, and default Buddy asset
- app-safe Buddy appearance contract for pixel/ascii modes and 64x64 animation states
- companion contracts, consent-first policy, and iBeMore app bridge contracts
- runtime engine, message state, tool calls, and tool registry
- Buddy profile, care, and training domain helpers
- local adapters for Buddy Brain, Omni, Prismtek app events, and vault-style retrieval
- note index, skill registry, automation registry, sandbox policy, app bridge contracts, gateway contracts, and Omni config
- ecosystem integration registry and CI scaffolding

## Development

```bash
ruff check .
mypy src
pytest
buddy --help
buddy doctor
buddy generate --output my-buddy
```

## Licensing

Repository-owned code uses `LICENSE` unless a file or directory states otherwise. Hermes-derived code remains governed by the original MIT license and notices. Expanded ecosystem integrations must be audited before code is copied or substantially adapted.
