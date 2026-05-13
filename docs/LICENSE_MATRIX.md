# License Matrix

Buddy Agent combines Prismtek-owned source with possible Hermes Agent source and a broader ecosystem of related repositories. This matrix records ownership and licensing expectations before code is imported.

| Area | Source | License posture | Notes |
| --- | --- | --- | --- |
| Buddy Agent scaffold | `codysumpter-cloud/buddy-agent` | Prismtek Source Available License 1.0 | Current repo-owned code. |
| Hermes-derived runtime | `NousResearch/hermes-agent` | MIT License | Preserve upstream notices in copied/adapted files. |
| Buddy Brain imports | `codysumpter-cloud/buddy-brain` | Prismtek Source Available License 1.0 | Import only through explicit branches and notices. |
| Omni Buddy imports | `codysumpter-cloud/omni-buddy` | Verify per file before import | README declares MIT; repo-level license should be checked before code import. |
| Prismtek Apps imports | `codysumpter-cloud/prismtek-apps` | Prismtek Source Available License 1.0 | Product contracts and domain concepts preferred over direct UI code copy. |
| Knowledge Vault imports | `codysumpter-cloud/knowledge-vault` | Verify per file before import | Prefer adapters and data contracts first. |
| Expanded ecosystem imports | Repos listed in `docs/ECOSYSTEM_INTEGRATION_MAP.md` | Pending per-repo and per-file audit | Native reimplementation and adapters are preferred before vendoring. |
| Restricted experiment imports | `MoneyPrinterV2`, `bettingAI` | Pending license, legal, financial-risk, and safety audit | Disabled by default and must stay behind policy gates. |

## Expanded ecosystem rule

The expanded repo list is tracked in `docs/ECOSYSTEM_INTEGRATION_MAP.md`, `docs/ECOSYSTEM_LICENSE_AUDIT.md`, and `buddy_agent.ecosystem`.

A repo being public or open source does not remove license obligations. Before importing source:

1. Verify the license at repo and file level.
2. Preserve copyright and license notices.
3. Record copied/adapted paths in `THIRD_PARTY_NOTICES.md`.
4. Update this matrix with the actual license posture.
5. Add tests and docs for the enabled integration.

## Rules

- Do not mix copied source without preserving its original license header or notice.
- Prefer adapters over direct copies when crossing product/runtime boundaries.
- Keep Hermes-derived files compatible with their MIT obligations.
- Keep Prismtek-owned commercial restrictions visible for repository-owned code.
- Keep restricted experiment integrations disabled by default.
- Update this matrix before merging any import branch.
