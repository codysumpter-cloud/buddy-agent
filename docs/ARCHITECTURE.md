# Architecture

Buddy Agent is structured as a modular agent runtime with explicit boundaries between upstream runtime behavior, Buddy product concepts, operator policy, local/offline hardware behavior, and knowledge retrieval.

## Layers

```text
Clients
  CLI, messaging gateway, app bridge

Buddy Agent Core
  runtime loop, session state, tool registry, model router

Domain modules
  buddy lifecycle, memory, skills, automations, sandbox, Omni, knowledge vault

External systems
  model providers, local runtimes, Prismtek Apps, Buddy Brain, Knowledge Vault
```

## Module boundaries

### `buddy_agent.runtime`

Owns the agent runtime shell: sessions, tool dispatch, model routing, and execution lifecycle. This is the primary landing zone for Hermes-derived runtime concepts.

### `buddy_agent.buddy`

Owns Buddy-native product concepts: archetypes, care, training, appearance profiles, sparring, and trade packages. It should remain serializable and app-friendly.

### `buddy_agent.omni`

Owns local/offline and Omni-backed routing. It should expose a narrow adapter instead of leaking hardware or transport details into the core runtime.

### `buddy_agent.app_bridge`

Owns relay contracts between Buddy Agent and Prismtek Apps. It should not import mobile UI code directly.

### `buddy_agent.memory`

Owns memory APIs and retrieval boundaries. Knowledge Vault integration belongs behind provider interfaces here.

### `buddy_agent.skills`

Owns skill metadata, execution contracts, and import strategy for Buddy Brain skill packs and Hermes-style skills.

### `buddy_agent.sandbox`

Owns execution backends, approval policy hooks, and command isolation.

## Security defaults

- No secrets committed to the repo.
- No network transport enabled by default.
- Destructive tool execution requires explicit policy gates.
- App-facing adapters should use typed, sanitized contracts.
- Imported upstream code must be reviewed before being wired to secrets, shell execution, or persistent storage.

## First integration sequence

1. Keep this scaffold passing tests.
2. Import Hermes source into an upstream branch with no rebrand changes.
3. Add a rebrand branch that renames package, CLI, config, and docs.
4. Add Buddy Brain adapters.
5. Add Omni Buddy local/offline adapters.
6. Add Prismtek Apps relay contracts.
7. Add Knowledge Vault retrieval provider.
