# Test Tonight

This guide gets Buddy Agent running locally and syncs the reference repositories for integration review.

## 1. Clone and install

```bash
git clone https://github.com/codysumpter-cloud/buddy-agent.git
cd buddy-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2. Run scaffold checks

```bash
buddy doctor
ruff check .
mypy src
pytest
```

Expected scaffold behavior:

- `buddy doctor` reports runtime, local Buddy Brain adapter, local Omni adapter, local app bridge, and local vault provider checks.
- Tests validate runtime, skills, automations, sandbox policy, config, local adapters, ecosystem registry, and reference manifest.

## 3. Sync reference repositories locally

```bash
python scripts/sync_reference_repos.py
```

This clones or updates reference repositories into `reference_repos/`. That directory is ignored by git.

Dry run:

```bash
python scripts/sync_reference_repos.py --dry-run
```

After sync, inspect:

```bash
cat reference_repos/REFERENCE_REPOS.md
```

## 4. What is testable tonight

You can test:

- Python package installation.
- `buddy` CLI startup.
- `buddy doctor` scaffold health checks.
- typed runtime/tool registry behavior.
- Buddy profile care/training model.
- local retrieval provider behavior.
- app event contract behavior.
- ecosystem/reference registry coverage.
- local reference repo sync.

## 5. What is not complete yet

The full Hermes Agent runtime and expanded ecosystem repos are not yet vendored or fully reimplemented inside `src/buddy_agent/`.

Use `reference_repos/` as the working source pool for audited, module-by-module ports. Before copying source into Buddy Agent:

1. verify the source license;
2. preserve notices;
3. update `THIRD_PARTY_NOTICES.md` and `docs/LICENSE_MATRIX.md`;
4. add tests;
5. keep risky integrations disabled by default.

## 6. Recommended next porting order

1. Hermes Agent runtime entrypoints and config.
2. Hermes memory/skills/scheduler contracts.
3. Buddy Brain operator layer.
4. Agent Memory and Knowledge Vault retrieval.
5. UI/control surfaces.
6. MCP and creative systems.
7. Restricted experiments only after explicit safety and legal review.
