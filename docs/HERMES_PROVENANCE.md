# Hermes Provenance

Buddy Agent is intended to use Hermes Agent as a reference runtime and possible upstream source.

## Upstream

- Name: Hermes Agent
- Repository: `NousResearch/hermes-agent`
- License: MIT
- Copyright: Copyright (c) 2025 Nous Research

## Current import status

The current Buddy Agent scaffold does not vendor the Hermes Agent source tree. It records the intended integration boundary and legal notices first.

## Required process for importing Hermes code

1. Import upstream source in a dedicated branch.
2. Preserve original MIT license and copyright notices.
3. Keep a clear commit message naming the upstream source and commit/ref.
4. Avoid bulk rebranding before tests run against the unmodified import.
5. Rebrand package names, CLI names, docs, and config keys in a follow-up branch.
6. Update `THIRD_PARTY_NOTICES.md` and `docs/LICENSE_MATRIX.md` when code is copied or substantially adapted.

## Rebrand boundaries

Allowed rebrand targets:

- CLI command: `hermes` to `buddy`
- Package/project naming: `hermes-agent` to `buddy-agent`
- User-facing docs and config namespaces where the runtime has been adapted

Do not remove upstream attribution from copied or adapted Hermes files.
