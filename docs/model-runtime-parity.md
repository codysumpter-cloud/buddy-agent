# Model Runtime Parity

Status: Buddy Agent runtime contract  
Created: 2026-06-15

Buddy Agent owns the executable side of model-runtime parity. The typed registry lives at:

`src/buddy_agent/model_runtime_parity.py`

It tracks hosted model capabilities, OpenMythos/OpenFable architecture coverage, and Buddy target status without claiming model equivalence.

## Sources

- `https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5`
- `https://github.com/kyegomez/OpenMythos`
- `https://github.com/lovestaco/OpenFable`
- `https://github.com/anthropic-fable/claude-fable-5`

## Runtime ownership

- provider boundaries
- capability ledger
- effort controls
- guarded tool runtime
- model route receipts
- conservative feature labels

## Next code steps

1. Add a `buddy model-parity` CLI command.
2. Add tests for `missing_buddy_capabilities()`.
3. Add provider response normalization for fallback/degraded modes.
4. Add effort preset objects.
5. Add context-manager contracts for compaction and tool-result clearing.
