"""CLI for the Buddy product spine contract."""

from __future__ import annotations

import sys

from .product_spine import product_spine_json, product_spine_summary_lines, validate_product_spine

PRODUCT_SPINE_USAGE = "Usage: buddy-product-spine [summary|json|validate]"


def run_product_spine_command(parts: list[str]) -> int:
    """Print or validate the canonical Buddy product spine."""
    subcommand = parts[0] if parts else "summary"

    if subcommand == "summary":
        for line in product_spine_summary_lines():
            print(line)
        return 0

    if subcommand == "json":
        print(product_spine_json())
        return 0

    if subcommand == "validate":
        errors = validate_product_spine()
        if errors:
            for error in errors:
                print(f"fail product-spine: {error}")
            return 1
        print("ok product-spine: app, runtime, brain, workspace, browser, and receipts are linked")
        return 0

    print(PRODUCT_SPINE_USAGE)
    return 2


def main(argv: list[str] | None = None) -> int:
    """Run the Buddy product spine CLI."""

    return run_product_spine_command(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
