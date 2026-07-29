# Prismtek Buddy Stack

This repository is the **guarded execution boundary** of the Prismtek Buddy Agent Platform. KnowledgeVault is durable memory, Buddy Brain is governance and economics, BUAP compiles portable policy, Omni Buddy owns local/device runtime, and Prismtek Apps owns product surfaces.

The machine-readable declaration is [`prismtek.component.json`](prismtek.component.json). The canonical topology is maintained in the BUAP stack manifest.

## Trust Fabric

Buddy Agent accepts cited retrieval output from an external provider, normalizes it into a provider-neutral evidence bundle, applies trust/freshness/conflict policy, and refuses to equate generated text with verified work.

```text
retrieval evidence
      ↓
evidence-bundle.json
      ↓
policy-decision.json
      ↓
guarded execution + artifact verification
      ↓
execution-receipt.json
memory-event.json
task-economics.json
```

Mitosis Cortex is supported as an optional public-contract adapter. It is not a hard dependency and does not own Prismtek policy, execution, verification, or durable-record authority.

See [`docs/TRUST_FABRIC.md`](docs/TRUST_FABRIC.md) for the executable demo.
