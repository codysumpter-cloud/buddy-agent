# Import Plan

Buddy Agent should be built through small reviewable branches instead of one large copy and rename commit.

## Phase 0: Scaffold

Status: started.

- README and boundaries
- License and notices
- Hermes provenance
- Architecture and parity docs
- Installable Python package placeholder
- CI, lint, type checking, and tests

## Phase 1: Hermes reference import

Branch: `import/hermes-agent-reference`

Import Hermes Agent into a staging path with minimal changes. Preserve upstream MIT notices. Record the upstream commit SHA before rebranding anything.

## Phase 2: Buddy rebrand

Branch: `rebrand/buddy-runtime`

Rename the package, CLI, docs, and config namespace from Hermes-oriented names to Buddy-oriented names while keeping attribution intact.

## Phase 3: Buddy Brain integration

Branch: `integrate/buddy-brain`

Map operator context, council posture, runbooks, memory docs, and skill packs into the adapter boundaries.

## Phase 4: Omni Buddy integration

Branch: `integrate/omni-buddy`

Add local/offline model routing, voice/vision contracts, transport policy, and runtime doctor checks behind adapters.

## Phase 5: Prismtek Apps integration

Branch: `integrate/prismtek-apps`

Add Buddy lifecycle contracts, app relay events, appearance profiles, sparring, and trade package schemas.

## Phase 6: Knowledge Vault integration

Branch: `integrate/knowledge-vault`

Add retrieval providers, source records, citation metadata, and vault-backed memory policies.

## Release gate

Do not claim feature parity until CI passes, notices are updated, the license matrix is current, and each parity item has tests or validation commands.
