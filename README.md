# Buddy Agent

Native Buddy runtime for the Prismtek / Hermes ecosystem.

## Visuals

- ASCII Buddy mascot: `assets/buddy-agent-mascot.svg`
- Pixel Buddy mascot: `assets/default-buddy.svg`
- Status badges: `assets/badges/`

## Install

```bash
git clone https://github.com/codysumpter-cloud/buddy-agent.git
cd buddy-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
buddy doctor
buddy smoke
buddy alpha
```

## Alpha Runtime Plus

```bash
buddy chat "hello buddy"
buddy app-chat "hello from widget" --surface widget
buddy remember "Prismtek likes clean runtime seams"
buddy recall "runtime"
buddy skill --skill caps "buddy alpha"
```

The Alpha Runtime Plus path wires Buddy-native runtime config, backend execution, persistent memory, vault-style retrieval, Buddy Brain operator context, local Omni routing, Buddy template loading, app bridge eventing, built-in skills, and companion permission policy into one runnable local path.

This is still an alpha milestone. It is not full Hermes Agent or full ecosystem feature parity. Reference repositories are tracked and mapped, but each source capability should only be marked complete after it is ported, rebranded, wired, tested, documented, and license-audited.

## Generate a Buddy

```bash
buddy generate --output my-buddy
```

Generated Buddies support pixel and ASCII render modes, idle/happy/thinking/sleepy states, and a centered 64x64 frame contract.

## Version Tracker

| Track | Status |
| --- | --- |
| Runtime | Alpha Runtime Plus branch |
| Package | `0.1.0` alpha scaffold |
| CLI | `buddy` |
| Alpha path | `buddy alpha`, `chat`, `app-chat`, `remember`, `recall`, `skill`, `parity` |
| Runtime config | JSON loader with safe local defaults |
| Backend execution | callable local template backend boundary |
| Memory | persistent JSON-backed local memory |
| Retrieval | local vault-style provider backed by note index |
| Buddy Brain layer | local operator context adapter |
| Omni routing | local callable backend adapter, provider-ready seam |
| App bridge route | typed `app-chat` route and in-process event bridge |
| Appearance | pixel and ASCII Buddy modes |
| Companion shell | loads and validates `templates/default-buddy/buddy.json` |
| iBeMore | typed app bridge contracts started |
| Hermes reference | tracked reference; source parity not yet complete |
| Restricted experiments | disabled by default |

## Current Status

Implemented alpha pieces:

- `buddy` CLI with status, doctor, smoke, alpha, chat, app-chat, remember, recall, skill, parity, and generate commands
- runnable local Alpha Runtime Plus composition
- runtime config loader and backend execution seam
- persistent JSON-backed local memory
- local vault-style retrieval provider
- local Buddy Brain operator context adapter
- local Omni-style routing adapter backed by the runtime backend seam
- typed app bridge chat route and local event bridge
- built-in summarize and caps skills
- app icon asset, README mascot asset, and default Buddy asset
- app-safe Buddy appearance contract for pixel/ascii modes and 64x64 animation states
- companion shell loader for the canonical default Buddy template
- companion contracts, consent-first policy, and iBeMore app bridge contracts
- runtime engine, message state, tool calls, and tool registry
- Buddy profile, care, and training domain helpers
- note index, skill registry, automation registry, sandbox policy, app bridge contracts, gateway contracts, and Omni config
- ecosystem integration registry and CI scaffolding

Still not claimed complete:

- full Hermes Agent source feature parity
- full Buddy Brain operator/council parity
- full AgentMemory or Knowledge Vault parity
- full Omni local model/voice/vision parity
- full Prismtek Apps or iBeMore app integration
- restricted experiment enablement

## Development

```bash
ruff check .
mypy src
pytest
buddy --help
buddy doctor
buddy smoke
buddy alpha
buddy app-chat "hello from app" --surface widget
buddy generate --output my-buddy
```

## Licensing

Repository-owned code uses `LICENSE` unless a file or directory states otherwise. Expanded ecosystem integrations must be audited before code is copied or substantially adapted.
