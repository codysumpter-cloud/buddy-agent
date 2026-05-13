<p align="center">
<pre>
  ____            _     _          _                    _
 | __ ) _   _  __| | __| |_   _   / \   __ _  ___ _ __ | |_
 |  _ \| | | |/ _` |/ _` | | | | / _ \ / _` |/ _ \ '_ \| __|
 | |_) | |_| | (_| | (_| | |_| |/ ___ \ (_| |  __/ | | | |_
 |____/ \__,_|\__,_|\__,_|\__, /_/   \_\__, |\___|_| |_|\__|
                           |___/        |___/
</pre>
</p>

<h1 align="center">Buddy Agent</h1>

<p align="center">
  <strong>A native Buddy-branded agent runtime for the Prismtek / Hermes ecosystem.</strong>
</p>

<p align="center">
  <a href="https://github.com/codysumpter-cloud/buddy-agent/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/codysumpter-cloud/buddy-agent/ci.yml?branch=main&label=CI&style=for-the-badge" alt="CI"></a>
  <a href="https://github.com/codysumpter-cloud/buddy-agent/releases"><img src="https://img.shields.io/github/v/release/codysumpter-cloud/buddy-agent?include_prereleases&label=Release&style=for-the-badge" alt="Release"></a>
  <a href="https://github.com/codysumpter-cloud/buddy-agent/commits/main"><img src="https://img.shields.io/github/last-commit/codysumpter-cloud/buddy-agent?style=for-the-badge" alt="Last Commit"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Prismtek%20Source%20Available-blueviolet?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <a href="#download--install">Download</a> •
  <a href="#version-tracker">Version Tracker</a> •
  <a href="#what-it-is">What It Is</a> •
  <a href="#ecosystem-scope">Ecosystem Scope</a> •
  <a href="#development">Development</a>
</p>

---

## Download / Install

Buddy Agent is not published as a package yet. Install from source for now:

```bash
git clone https://github.com/codysumpter-cloud/buddy-agent.git
cd buddy-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
buddy doctor
```

One-line source install:

```bash
git clone https://github.com/codysumpter-cloud/buddy-agent.git && cd buddy-agent && python -m venv .venv && source .venv/bin/activate && pip install -e .[dev] && buddy doctor
```

## Version Tracker

| Track | Version / status |
| --- | --- |
| Buddy Agent package | `0.1.0` scaffold |
| CLI | `buddy` |
| Runtime status | Native scaffold, not full Hermes port yet |
| Hermes reference | Planned import from `NousResearch/hermes-agent` |
| Ecosystem registry | Expanded Prismtek/Hermes repo set tracked in `buddy_agent.ecosystem` |
| Restricted experiments | Disabled by default |

## What It Is

Buddy Agent is a Buddy-branded agent runtime scaffold for Prismtek.

The project is intended to combine a Hermes Agent-derived runtime with Buddy Brain operator contracts, Omni Buddy local/offline capabilities, Prismtek Apps product contracts, Knowledge Vault retrieval patterns, and the broader Prismtek/Hermes creative/runtime ecosystem.

## Goals

- Rebrand the Hermes Agent reference runtime as `buddy-agent` and `buddy` while preserving upstream notices.
- Keep runtime, app UI, operator policy, and knowledge storage behind explicit adapter boundaries.
- Add Buddy lifecycle concepts such as care, training, appearance, sparring, trade packages, and app relay contracts.
- Support local/offline and Omni-backed operation without forcing every install into one runtime mode.
- Provide native landing zones for UI, MCP, pixel/creative, mythos, model, discovery, compression, and restricted experiment integrations.

## Ecosystem Scope

| System | Role |
| --- | --- |
| `NousResearch/hermes-agent` | Reference agent runtime and MIT-licensed upstream source. |
| `codysumpter-cloud/buddy-brain` | Operator contracts, council posture, runbooks, skills, and workspace glue. |
| `codysumpter-cloud/omni-buddy` | Local/offline hardware agent, voice/vision loop, Omni routing, and transport resilience. |
| `codysumpter-cloud/prismtek-apps` | Buddy product lifecycle, app-facing protocol, care/training loop, and trade packages. |
| `codysumpter-cloud/knowledge-vault` | Retrieval corpus, source provenance, indexed knowledge, and vault-backed memory. |
| `codysumpter-cloud/awesome-hermes-agent` | Ecosystem discovery, maturity tags, release references, and integration ideas. |
| `codysumpter-cloud/caveman` | Brevity/compression skill ideas, memory compression, and terse agent modes. |
| Expanded ecosystem repos | UI, MCP, memory, creative, mythos, workspace, model, and restricted experiment integrations. |

## Package Layout

```text
buddy_agent/
  runtime/
  memory/
  skills/
  automations/
  gateway/
  sandbox/
  omni/
  buddy/
  app_bridge/
  ui/
  mcp/
  creative/
  mythos/
  models/
  experiments/
```

## Current Status

This repository is initialized as a provenance-safe native scaffold. It does not yet vendor the full Hermes source or claim full feature parity.

Implemented scaffold pieces include:

- `buddy` CLI with status and doctor commands
- runtime engine, message state, tool calls, and tool registry
- Buddy profile, care, and training domain helpers
- local adapters for Buddy Brain, Omni, Prismtek app events, and vault-style retrieval
- note index, skill registry, automation registry, sandbox policy, app bridge contracts, gateway contracts, and Omni config
- ecosystem integration registry for the expanded repo set
- CI for install, lint, type checking, and tests

See:

- `docs/HERMES_PROVENANCE.md`
- `docs/LICENSE_MATRIX.md`
- `docs/BUDDY_FEATURE_PARITY.md`
- `docs/ARCHITECTURE.md`
- `docs/IMPORT_PLAN.md`
- `docs/ECOSYSTEM_INTEGRATION_MAP.md`
- `docs/ECOSYSTEM_LICENSE_AUDIT.md`

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ruff check .
mypy src
pytest
buddy --help
buddy doctor
```

## Licensing

Repository-owned code uses the license in `LICENSE` unless a file or directory states otherwise. Hermes-derived code remains governed by the original MIT license and notices. Expanded ecosystem integrations must be audited before code is copied or substantially adapted. See `NOTICE`, `THIRD_PARTY_NOTICES.md`, `docs/LICENSE_MATRIX.md`, and `docs/ECOSYSTEM_LICENSE_AUDIT.md`.
