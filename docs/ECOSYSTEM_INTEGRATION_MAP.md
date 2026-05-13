# Ecosystem Integration Map

Buddy Agent is intended to become the native Buddy runtime that can absorb useful concepts from the broader Prismtek/Hermes ecosystem without turning into an unreviewed source dump.

## Import rule

Every repository listed here is an integration candidate, not automatically imported source. Before code is copied or substantially adapted:

1. Verify the repository license at the file level.
2. Preserve copyright and notices.
3. Add the source to `THIRD_PARTY_NOTICES.md` and `docs/LICENSE_MATRIX.md`.
4. Prefer native Buddy Agent modules and typed adapter contracts over direct vendoring.
5. Keep risky capabilities disabled by default until policy, tests, and docs exist.

## Native integration groups

| Group | Repositories | Native Buddy Agent landing zone | Notes |
| --- | --- | --- | --- |
| Hermes runtime ecosystem | `hermes-ecosystem`, `hermes-workspace`, `Hermes-Wiki` | `buddy_agent.runtime`, `buddy_agent.skills`, `buddy_agent.memory`, `docs/` | Runtime, workspace, docs, and agent operating patterns. |
| Discovery and ecosystem index | `awesome-hermes-agent` | `docs/`, future discovery registry | Curated ecosystem discovery, maturity tags, release references, and integration ideas. |
| Control and operator UI | `hermes-control-interface`, `hermes-webui`, `hermes-hudui` | `buddy_agent.gateway`, `buddy_agent.app_bridge`, future `buddy_agent.ui` | Build native contracts first; avoid coupling runtime to a specific UI framework. |
| Product app layer | `prismtek-apps` | `buddy_agent.buddy`, `buddy_agent.app_bridge` | Buddy lifecycle, care, training, appearance, sparring, trade packages, OAuth relay. |
| Memory and knowledge | `agentmemory`, `knowledge-vault` | `buddy_agent.memory`, `LocalKnowledgeVaultProvider` | Retrieval, source records, recall, memory write policy. |
| Skills and compression | `caveman` | `buddy_agent.skills` | Terse-output skill ideas, memory compression, statusline concepts, and agent brevity modes. |
| Tools and MCP | `arcade-mcp`, `pixellab-mcp` | `buddy_agent.skills`, future `buddy_agent.mcp` | Tool registry, MCP adapters, permission boundaries. |
| Pixel and creative systems | `LibreSprite`, `pixellab-js`, `tamagoscii` | `buddy_agent.buddy`, future `buddy_agent.creative` | Pixel/avatar/ASCII appearance workflows and Buddy customization. |
| Mythos and narrative layer | `OpenMythos`, `symphony` | future `buddy_agent.mythos` | Lore, archetypes, orchestration, narrative context. |
| Model/runtime experiments | `gemma` | `buddy_agent.omni`, future `buddy_agent.models` | Local model profiles and routing experiments. |
| Monetization and finance-like experiments | `MoneyPrinterV2`, `bettingAI` | future `buddy_agent.experiments` | Disabled by default. Requires legal, platform, financial-risk, and safety review before runtime exposure. |

## Safety posture

- Finance, betting, scraping, monetization, and autonomous publishing workflows must not be enabled by default.
- Any workflow that touches money, ads, betting, affiliate content, or account automation needs explicit policy gates and documentation.
- UI repos should contribute contracts and UX ideas before runtime code imports.
- Creative repos should contribute asset pipelines and schemas before native rendering is attempted.
- Compression/terse-output integrations should preserve technical accuracy and never hide safety-critical detail.

## Suggested phase sequence

1. Verify licenses and notices for all candidate repos.
2. Add native module namespaces for UI, MCP, creative, mythos, models, and experiments.
3. Add adapter interfaces and local no-op implementations.
4. Import only small, tested pieces with clear provenance.
5. Close feature parity items only after tests and docs land.
