# Skill Policy

Buddy-Agent skills use `SKILL.md` manifests for metadata and risk classification. Manifest loading is metadata-only: Buddy-Agent must not execute arbitrary code from `SKILL.md`.

## Skill paths

| Path | Purpose | Public default |
| --- | --- | --- |
| `skills/public` | Safe demo and reviewed public skills | yes |
| `skills/experimental` | Work-in-progress integrations | no |
| `skills/private` | Local-only private skills | no |

`BUDDY_SKILLS_PATH` defaults to `skills/public`.

## Required manifest fields

```yaml
---
name: caps
description: Uppercase input text locally.
buddy:
  risk_class: draft-only
  auto_executable: false
  requires_explicit_approval: false
---
```

Required fields:

- `name`
- `description`

Optional fields:

- `version`
- `author`
- `license`
- `platforms`
- `metadata`
- `buddy.risk_class`
- `buddy.auto_executable`
- `buddy.requires_explicit_approval`

Descriptions must be under 1024 characters. Names must be stable manifest identifiers using letters, numbers, dots, underscores, or hyphens.

## Risk classes

| Risk class | Meaning | Default policy |
| --- | --- | --- |
| `read-only` | Reads local/public-safe data only | allow |
| `draft-only` | Produces text or plans without taking action | allow |
| `write` | Writes local files or state | confirm |
| `external-action` | Calls an outside service or account-bound action | confirm |
| `destructive` | Deletes, overwrites, or irreversibly mutates data | deny-by-default |
| `money` | Money, trading, betting, deposits, withdrawals, wallet signing | deny-by-default |
| `identity` | Identity, account, profile, authentication, or impersonation risk | deny-by-default |
| `location` | Uses precise location or location-derived actions | confirm |
| `credential` | Reads, stores, transforms, or transmits secrets | deny |
| `repo-mutation` | Commits, pushes, opens PRs, or mutates repositories | confirm |

## Public skill restrictions

Do not add these to `skills/public`:

- signed-in browser automation;
- live social posting;
- credential inventory;
- gambling, betting, trading, prediction-market execution;
- wallet signing;
- deposit or withdrawal flows;
- destructive filesystem or account actions;
- private local environment paths.

Prefer abstract adapter contracts and placeholders until a skill has docs, tests, audit notes, and explicit approval behavior.
