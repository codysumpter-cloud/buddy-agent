# Contributing to Buddy-Agent

Buddy-Agent is the guarded execution layer for Prismtek's Agentic OS. Contributions should improve runnable local behavior, safety boundaries, documentation, tests, and public-alpha clarity without overclaiming autonomy.

## Ground rules

- Do not commit secrets, tokens, cookies, private paths, account IDs, OAuth secrets, or generated local state.
- Do not add live account automation as a public/default feature.
- Do not add money-action, gambling, trading, prediction-market, wallet-signing, deposit, or withdrawal flows.
- Keep risky skills out of `skills/public`.
- Prefer adapter contracts and placeholder interfaces over live account integrations.
- Preserve existing license notices and MIT notices for Hermes-derived code.
- Do not copy code from AGPL or otherwise restricted repositories.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Required checks

```bash
ruff check .
mypy src
pytest
buddy doctor
buddy smoke
buddy alpha
buddy parity
buddy skills validate
```

## Pull requests

Use feature branches. Do not push directly to `main`.

A good PR should include a clear summary, safety posture changes, tests run, known limitations, and any future work moved out of scope.

## Skill contributions

Public skills must include a `SKILL.md` manifest with safe frontmatter and an explicit Buddy risk class. Manifest parsing is metadata-only and must not execute code.

Risky integrations belong in `skills/experimental` or private local paths until audited and documented.
