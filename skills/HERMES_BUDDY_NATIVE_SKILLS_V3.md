# Hermes/Buddy Native Skills v3

This branch adds native Buddy-compatible `SKILL.md` files under `skills/native/`.

## Included capability groups

- Social content planning and draft generation.
- Modular content factory workflows.
- Read-only public social insight analysis.
- Read-only bookmark and article digests.
- Memory and KnowledgeVault synthesis.
- Pre-call context preparation.
- Responsible risk education and model review workflows.

## Runtime policy

Buddy may read all skills. Read-only skills may be auto-selected. Anything that changes an outside account, publishes content, writes to a repo, changes memory, or touches a regulated domain remains approval-gated and adapter-mediated.

## Verification

Each native skill uses Hermes-style YAML frontmatter at byte 0, including `name`, `description`, `version`, `author`, `license`, `platforms`, and `metadata`.
