# License Matrix

Buddy Agent combines Prismtek-owned source with possible MIT-licensed Hermes Agent source. This matrix records ownership and licensing expectations before code is imported.

| Area | Source | License posture | Notes |
| --- | --- | --- | --- |
| Buddy Agent scaffold | `codysumpter-cloud/buddy-agent` | Prismtek Source Available License 1.0 | Current repo-owned code. |
| Hermes-derived runtime | `NousResearch/hermes-agent` | MIT License | Preserve upstream notices in copied/adapted files. |
| Buddy Brain imports | `codysumpter-cloud/buddy-brain` | Prismtek Source Available License 1.0 | Import only through explicit branches and notices. |
| Omni Buddy imports | `codysumpter-cloud/omni-buddy` | Verify per file before import | README declares MIT; repo-level license should be checked before code import. |
| Prismtek Apps imports | `codysumpter-cloud/prismtek-apps` | Prismtek Source Available License 1.0 | Product contracts and domain concepts preferred over direct UI code copy. |
| Knowledge Vault imports | `codysumpter-cloud/knowledge-vault` | Verify per file before import | Prefer adapters and data contracts first. |

## Rules

- Do not mix copied source without preserving its original license header or notice.
- Prefer adapters over direct copies when crossing product/runtime boundaries.
- Keep Hermes-derived files compatible with their MIT obligations.
- Keep Prismtek-owned commercial restrictions visible for repository-owned code.
- Update this matrix before merging any import branch.
