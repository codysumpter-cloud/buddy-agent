# Security Policy

Buddy-Agent is alpha software. It is intended for guarded local execution experiments and public review, not unsupervised production automation.

## Reporting security issues

Do not open public GitHub issues, discussions, pull requests, screenshots, or logs containing secrets or private operational details.

Secrets include API keys, tokens, cookies, passwords, OAuth client secrets, private account identifiers, wallet material, session data, private file paths, and anything copied from a signed-in browser profile.

For now, report suspected vulnerabilities privately to the project maintainer. Include a minimal description, the affected area, and safe reproduction steps that do not expose credentials or private accounts.

## Public alpha safety posture

Buddy-Agent defaults to local/offline behavior:

- `BUDDY_PROVIDER=local`
- `BUDDY_NETWORK_ENABLED=false`
- `BUDDY_APPROVAL_MODE=manual`
- `BUDDY_SKILLS_PATH=skills/public`

No network provider, browser session automation, live social posting, wallet signing, deposit, withdrawal, trading, gambling, prediction-market, or credential inventory feature is enabled by default.

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x alpha | Security fixes best-effort |

## Handling secrets locally

Use `.env.example` as a placeholder template only. Put real local settings in ignored files such as `.env.local`, never in committed examples or docs.

Before public release, run secret scans against both the current tree and full history, then manually review docs, tests, examples, receipts, and skill manifests for private paths or account details.
