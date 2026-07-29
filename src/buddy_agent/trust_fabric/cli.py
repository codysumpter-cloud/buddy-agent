"""Command-line interface for the Prismtek Trust Fabric."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .normalizer import load_json
from .pipeline import evaluate_retrieval, finalize_run


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="buddy-trust",
        description="Evaluate retrieval evidence before guarded execution.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate = sub.add_parser(
        "evaluate",
        help="Normalize retrieval output and make an admissibility decision.",
    )
    evaluate.add_argument("input", type=Path)
    evaluate.add_argument("--out", type=Path, required=True)
    evaluate.add_argument("--as-of", help="ISO-8601 evaluation time for deterministic tests.")

    finalize = sub.add_parser(
        "finalize",
        help="Verify an artifact and emit the final receipt/event/economics records.",
    )
    finalize.add_argument("output_dir", type=Path)
    finalize.add_argument("--artifact", type=Path, required=True)
    finalize.add_argument("--reviewer", required=True)
    finalize.add_argument("--review-approved", action="store_true")
    finalize.add_argument(
        "--security-gate",
        choices=("pass", "review", "block", "not-run"),
        default="pass",
    )
    finalize.add_argument("--provider", default="unknown")
    finalize.add_argument("--model", default="unknown")
    finalize.add_argument("--attempts", type=int, default=1)
    finalize.add_argument("--model-cost", type=float, default=0.0)
    finalize.add_argument("--tool-cost", type=float, default=0.0)
    finalize.add_argument("--elapsed-ms", type=int, default=0)
    finalize.add_argument("--human-review-minutes", type=float, default=0.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "evaluate":
        result = evaluate_retrieval(load_json(str(args.input)), args.out, as_of=args.as_of)
    else:
        result = finalize_run(
            args.output_dir,
            args.artifact,
            reviewer=args.reviewer,
            review_approved=args.review_approved,
            security_gate=args.security_gate,
            provider=args.provider,
            model=args.model,
            attempts=args.attempts,
            model_cost=args.model_cost,
            tool_cost=args.tool_cost,
            elapsed_ms=args.elapsed_ms,
            human_review_minutes=args.human_review_minutes,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
