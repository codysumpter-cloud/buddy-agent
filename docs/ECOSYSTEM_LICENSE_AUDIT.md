# Ecosystem License Audit

This audit tracks license/provenance verification for the expanded Buddy Agent ecosystem integrations.

## Rule

A repository being public or open source does not by itself mean Buddy Agent can remove attribution, erase license terms, or copy code without notices. Each import must preserve the original license and copyright terms.

## Candidate repositories

| Repository | Planned use | Status | Default enablement |
| --- | --- | --- | --- |
| `codysumpter-cloud/hermes-ecosystem` | Runtime ecosystem patterns | Pending license/file audit | Disabled |
| `codysumpter-cloud/prismtek-apps` | Product contracts and Buddy lifecycle | Known Prismtek source-available from existing audit | Disabled |
| `codysumpter-cloud/agentmemory` | Memory and recall patterns | Pending license/file audit | Disabled |
| `codysumpter-cloud/hermes-control-interface` | Operator/control UI contracts | Pending license/file audit | Disabled |
| `codysumpter-cloud/MoneyPrinterV2` | Experimental monetization workflows | Pending license/file audit and safety review | Disabled, restricted |
| `erikbohne/bettingAI` | Experimental betting/forecasting reference | Pending license/file audit and safety review | Disabled, restricted |
| `codysumpter-cloud/hermes-workspace` | Workspace layout and runtime patterns | Pending license/file audit | Disabled |
| `codysumpter-cloud/arcade-mcp` | MCP tooling patterns | Pending license/file audit | Disabled |
| `codysumpter-cloud/hermes-webui` | Web UI/control ideas | Pending license/file audit | Disabled |
| `codysumpter-cloud/hermes-hudui` | HUD UI/control ideas | Pending license/file audit | Disabled |
| `codysumpter-cloud/gemma` | Model/runtime experiments | Pending license/file audit | Disabled |
| `codysumpter-cloud/symphony` | Orchestration/mythos patterns | Pending license/file audit | Disabled |
| `codysumpter-cloud/LibreSprite` | Pixel/sprite editing reference | Pending license/file audit | Disabled |
| `codysumpter-cloud/Hermes-Wiki` | Documentation and knowledge base | Pending license/file audit | Disabled |
| `codysumpter-cloud/OpenMythos` | Mythos/lore system | Pending license/file audit | Disabled |
| `codysumpter-cloud/tamagoscii` | ASCII Buddy appearance loop | Pending license/file audit | Disabled |
| `codysumpter-cloud/pixellab-mcp` | PixelLab MCP tooling | Pending license/file audit | Disabled |
| `codysumpter-cloud/pixellab-js` | PixelLab UI/creative tooling | Pending license/file audit | Disabled |

## Restricted integration policy

`MoneyPrinterV2` and `bettingAI` are restricted. They may be studied as references, but Buddy Agent must not expose autonomous money, ad, affiliate, trading, gambling, or betting workflows by default.

Before any restricted integration becomes callable:

1. Add policy gates.
2. Add explicit user confirmation flows.
3. Add compliance notes.
4. Add tests proving the feature is disabled by default.
5. Add docs that explain risks and limitations.

## Next audit step

For each repository, record:

- license file path and SPDX-style summary when available;
- copied or adapted paths;
- original copyright holder;
- notice text required in Buddy Agent;
- whether the integration is native reimplementation, adapter-only, or vendored source.
