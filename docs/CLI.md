# Buddy-Agent CLI

The `buddy` command exposes the public-alpha runtime surface.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Core commands

```bash
buddy --version
buddy doctor
buddy status
buddy smoke
buddy alpha
buddy parity
```

## Runtime commands

```bash
buddy chat "hello"
buddy remember "test memory"
buddy recall "test"
buddy skill --skill caps "buddy"
```

Runtime commands use local/offline defaults unless explicitly configured otherwise.

## Skill manifest commands

```bash
buddy skills list
buddy skills validate
buddy skills inspect caps
```

Skill commands read `BUDDY_SKILLS_PATH`, defaulting to `skills/public`.

## Provider commands

```bash
buddy providers list
```

The public alpha provider registry contains `local` by default. Unknown providers fall back to local while networking is disabled.

## Receipt commands

```bash
buddy receipts path
buddy --receipts chat "hello"
```

Receipts are local sanitized summaries. They should not contain prompts, secrets, account identifiers, cookies, tokens, or private keys.
