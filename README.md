# Buddy Agent

Buddy Agent is a Buddy-branded agent runtime scaffold for Prismtek.

The project is intended to combine a Hermes Agent-derived runtime with Buddy Brain operator contracts, Omni Buddy local/offline capabilities, Prismtek Apps product contracts, Knowledge Vault retrieval patterns, and the broader Prismtek/Hermes creative/runtime ecosystem.

## Goals

- Rebrand the Hermes Agent reference runtime as `buddy-agent` and `buddy` while preserving upstream notices.
- Keep runtime, app UI, operator policy, and knowledge storage behind explicit adapter boundaries.
- Add Buddy lifecycle concepts such as care, training, appearance, sparring, trade packages, and app relay contracts.
- Support local/offline and Omni-backed operation without forcing every install into one runtime mode.
- Provide native landing zones for UI, MCP, pixel/creative, mythos, model, and restricted experiment integrations.

## Source systems

| System | Role |
| --- | --- |
| `NousResearch/hermes-agent` | Reference agent runtime and MIT-licensed upstream source. |
| `codysumpter-cloud/buddy-brain` | Operator contracts, council posture, runbooks, skills, and workspace glue. |
| `codysumpter-cloud/omni-buddy` | Local/offline hardware agent, voice/vision loop, Omni routing, and transport resilience. |
| `codysumpter-cloud/prismtek-apps` | Buddy product lifecycle, app-facing protocol, care/training loop, and trade packages. |
| `codysumpter-cloud/knowledge-vault` | Retrieval corpus, source provenance, indexed knowledge, and vault-backed memory. |
| Expanded ecosystem repos | UI, MCP, memory, creative, mythos, workspace, model, and restricted experiment integrations. |

## Planned package layout

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

## Current status

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
pytest
buddy --help
buddy doctor
```

## Licensing

Repository-owned code uses the license in `LICENSE` unless a file or directory states otherwise. Hermes-derived code remains governed by the original MIT license and notices. Expanded ecosystem integrations must be audited before code is copied or substantially adapted. See `NOTICE`, `THIRD_PARTY_NOTICES.md`, `docs/LICENSE_MATRIX.md`, and `docs/ECOSYSTEM_LICENSE_AUDIT.md`.
