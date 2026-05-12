# Buddy Agent

Buddy Agent is a Buddy-branded agent runtime scaffold for Prismtek.

The project is intended to combine a Hermes Agent-derived runtime with Buddy Brain operator contracts, Omni Buddy local/offline capabilities, Prismtek Apps product contracts, and Knowledge Vault retrieval patterns.

## Goals

- Rebrand the Hermes Agent reference runtime as `buddy-agent` and `buddy` while preserving upstream notices.
- Keep runtime, app UI, operator policy, and knowledge storage behind explicit adapter boundaries.
- Add Buddy lifecycle concepts such as care, training, appearance, sparring, trade packages, and app relay contracts.
- Support local/offline and Omni-backed operation without forcing every install into one runtime mode.

## Source systems

| System | Role |
| --- | --- |
| `NousResearch/hermes-agent` | Reference agent runtime and MIT-licensed upstream source. |
| `codysumpter-cloud/buddy-brain` | Operator contracts, council posture, runbooks, skills, and workspace glue. |
| `codysumpter-cloud/omni-buddy` | Local/offline hardware agent, voice/vision loop, Omni routing, and transport resilience. |
| `codysumpter-cloud/prismtek-apps` | Buddy product lifecycle, app-facing protocol, care/training loop, and trade packages. |
| `codysumpter-cloud/knowledge-vault` | Retrieval corpus, source provenance, indexed knowledge, and vault-backed memory. |

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
```

## Current status

This repository is initialized as a provenance-safe scaffold. It does not yet vendor the full Hermes source or claim feature parity.

See:

- `docs/HERMES_PROVENANCE.md`
- `docs/LICENSE_MATRIX.md`
- `docs/BUDDY_FEATURE_PARITY.md`
- `docs/ARCHITECTURE.md`

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
buddy --help
```

## Licensing

Repository-owned code uses the license in `LICENSE` unless a file or directory states otherwise. Hermes-derived code remains governed by the original MIT license and notices. See `NOTICE` and `THIRD_PARTY_NOTICES.md`.
