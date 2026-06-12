<p align="center">
  <img src="assets/buddy-agent-mascot.svg" alt="Buddy Agent animated ASCII mascot" width="280">
</p>

<h1 align="center">Buddy Agent</h1>

<p align="center"><strong>Guarded execution layer for Prismtek's Agentic OS.</strong></p>

<p align="center">
  <img src="assets/badges/runtime.svg" alt="Runtime: runnable alpha"><br>
  <img src="assets/badges/version.svg" alt="Version: 0.1.0 alpha"><br>
  <img src="assets/badges/license.svg" alt="License: Prismtek Source Available">
</p>

## What Buddy-Agent is

Buddy-Agent is the guarded execution layer for Prismtek's Agentic OS. It connects the runtime shell, skills, memory, policies, adapters, and receipts so the ecosystem has one safe local execution boundary to harden over time.

The current project is a **runnable alpha**. It is designed to be installed locally, inspected, tested, and extended behind conservative defaults.

## What Buddy-Agent is not

Buddy-Agent is not a finished autonomous production operator. It is not a live-account browser bot, trading bot, gambling bot, wallet signer, credential manager, or unsupervised agent runtime.

Public defaults do not include signed-in Safari automation, browser session automation, live social posting, credential inventory, gambling, trading, prediction-market execution, wallet signing, deposits, withdrawals, or money-action instructions.

## Alpha warning

This is alpha software. Expect rough edges, incomplete adapters, local-only defaults, and explicit approval boundaries. Use it for guarded development and review, not production automation.

## Safety model summary

Buddy-Agent defaults to local/offline execution:

```bash
BUDDY_PROVIDER=local
BUDDY_NETWORK_ENABLED=false
BUDDY_APPROVAL_MODE=manual
BUDDY_SKILLS_PATH=skills/public
```

Unknown providers fall back to the local provider while network execution is disabled. Receipts are local sanitized summaries and should not contain prompts, secrets, tokens, cookies, private keys, OAuth material, account identifiers, or browser session data.

Read the full model in [`docs/SAFETY_MODEL.md`](docs/SAFETY_MODEL.md).

## Skill approval model

Skills are described by `SKILL.md` manifests. Manifest parsing is metadata-only and does not execute arbitrary code.

Default policy:

| Risk class | Default |
| --- | --- |
| `read-only` | allow |
| `draft-only` | allow |
| `write` | confirm |
| `external-action` | confirm |
| `destructive` | deny-by-default |
| `money` | deny-by-default |
| `identity` | deny-by-default |
| `location` | confirm |
| `credential` | deny |
| `repo-mutation` | confirm |

Read the full policy in [`docs/SKILL_POLICY.md`](docs/SKILL_POLICY.md).

## Public-safe install

```bash
git clone <access-granted Buddy-Agent repository URL>
cd buddy-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env.local
```

`.env.local` is ignored. Do not commit real API keys, tokens, cookies, passwords, OAuth secrets, account IDs, private keys, or private local paths.

## Public-safe quickstart

```bash
buddy --version
buddy doctor
buddy status
buddy smoke
buddy alpha
buddy chat "hello buddy"
buddy remember "Buddy can keep local notes"
buddy recall "Buddy"
buddy skill --skill caps "buddy alpha"
buddy skills validate
buddy providers list
buddy receipts path
buddy parity
buddy-demo "Draft a safe project note"
```

## Buddy + Lil' Buddy orchestration demo

The local Buddy/Lil' Buddy scaffold lives in [`src/buddy_agent/orchestration/`](src/buddy_agent/orchestration/) with task, result, and review envelopes plus matching schemas in [`schemas/`](schemas/).

Run the no-secrets local demo:

```bash
buddy-demo "Draft a safe project note"
```

The command routes one prompt through Buddy as orchestrator, one Lil' Buddy worker, Buddy Review, and a final reviewed response. See [`docs/BUDDY_LIL_BUDDY_RUNTIME.md`](docs/BUDDY_LIL_BUDDY_RUNTIME.md).

Future prompts should follow the ecosystem default: use KnowledgeVault for durable knowledge, Buddy Brain for governance, Buddy Agent for runtime execution, and Omni Buddy for local embodied/device integrations.

## Generate a Buddy

```bash
buddy generate --output my-buddy
```

Generated Buddies support pixel and ASCII render modes, idle/happy/thinking/sleepy states, and a centered 64x64 frame contract.

## CLI docs

See [`docs/CLI.md`](docs/CLI.md) for the public-alpha command surface.

## Known limitations

- The default provider is local echo only.
- Network providers are not enabled by default.
- Public skills are demos and placeholders, not a complete skill registry.
- KnowledgeVault, Buddy-Brain, Omni, and app bridges are contract/future-work areas unless explicitly implemented and audited.
- Receipts are local files and are not a complete audit/compliance system.
- This repo is source-available and commercially restricted, not open-source under a permissive license.

## Ecosystem relationships

| Project/surface | Relationship |
| --- | --- |
| Buddy-Brain | Future bridge for startup/context handoff; not a public default live brain dependency. |
| KnowledgeVault | Future read-only retrieval adapter; public alpha includes a placeholder skill manifest only. |
| Omni-Buddy | Local bridge/fallback concepts exist; network bridge remains explicit future/audited work. |
| Prismtek Apps | Buddy-Agent can define app bridge contracts; live app/account actions are not public defaults. |
| Hermes | Buddy-Agent may preserve Hermes-compatible concepts and must preserve MIT notices for Hermes-derived code. |

## Version tracker

| Track | Status |
| --- | --- |
| Runtime | <img src="assets/status-dot.svg" width="12" alt="online"> runnable alpha |
| Package | `0.1.0` alpha scaffold |
| CLI | `buddy` |
| Provider | local/offline default |
| Memory | persistent JSON-backed local memory |
| Skills | public manifest validation and built-in demos |
| Receipts | local sanitized JSONL/JSON primitives |
| Appearance | pixel and ASCII Buddy modes |
| Companion | consent-first contracts started |
| iBeMore | typed app bridge contracts started |

## Development

```bash
ruff check .
mypy src
pytest
buddy --help
buddy doctor
buddy smoke
buddy alpha
buddy skills validate
buddy generate --output my-buddy
buddy-demo "Draft a safe project note"
```

## License summary

Buddy-Agent is source-available under the Prismtek Source Available License. Personal, educational, and non-commercial use is allowed under the repository license. Commercial use requires a separate written commercial license agreement from the copyright holder.

This summary is not a replacement for [`LICENSE`](LICENSE). Review [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) before public release or redistribution.
