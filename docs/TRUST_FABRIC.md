# Prismtek Trust Fabric

The Trust Fabric sits between retrieval and action. It accepts provider-shaped cited results, converts them to a stable evidence contract, applies admissibility policy, and refuses to call work verified until an artifact and security gate pass.

Mitosis Cortex is one optional adapter shape. The core package has no Mitosis dependency.

## Evaluate retrieval evidence

```bash
buddy-trust evaluate examples/mitosis-retrieval.json \
  --out build/trust-demo \
  --as-of 2026-07-29T12:00:00Z
```

Outputs:

- `evidence-bundle.json`
- `policy-decision.json`
- `execution-receipt.json` in an unverified state
- `memory-event.json` containing hashes and policy state, not raw prompts
- `provenance-report.md`

## Finalize a verified artifact

```bash
buddy-trust finalize build/trust-demo \
  --artifact build/result.md \
  --reviewer Cody \
  --review-approved \
  --security-gate pass \
  --provider openai \
  --model gpt-5.6 \
  --attempts 1 \
  --model-cost 0.12 \
  --tool-cost 0.01 \
  --elapsed-ms 42000 \
  --human-review-minutes 3
```

A blocked decision cannot be finalized. A review decision requires `--review-approved`. Finalization requires a real file and computes its SHA-256 digest.

## Provider input shape

The normalizer accepts canonical snake_case fields plus common provider aliases such as `universalId`, `sourceType`, `observedAt`, `validUntil`, and `trustTier`.

```json
{
  "provider": "mitosis-cortex",
  "taskId": "demo-1",
  "agentId": "buddy",
  "riskLevel": "high",
  "query": "Should this agent perform the action?",
  "sources": [
    {
      "universalId": "source-123",
      "excerpt": "Source text used only during evaluation.",
      "sourceType": "document",
      "observedAt": "2026-07-29T10:00:00Z",
      "validUntil": "2026-08-29T10:00:00Z",
      "confidence": 0.91,
      "trustTier": "verified",
      "contradicts": []
    }
  ]
}
```

## Default policy

- Missing evidence requires review and blocks high or critical risk.
- Explicit source conflicts require review and block high or critical risk.
- Stale authoritative evidence blocks high or critical risk.
- Low confidence requires corroboration.
- High-risk work needs a current authoritative or verified source with confidence of at least `0.7`.
- Raw prompts, credentials, browser state, and source excerpts do not enter receipts, memory events, or economics telemetry.

## Verification

```bash
pytest -q tests/test_trust_fabric.py
python -m py_compile src/buddy_agent/trust_fabric/*.py
```
