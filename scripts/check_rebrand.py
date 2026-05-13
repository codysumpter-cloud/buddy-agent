#!/usr/bin/env python3
"""Check Buddy Agent source files for unexpected legacy naming.

This does not fail on reference manifests or provenance docs. Those files are supposed
to mention upstream project names.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_DIRS = (ROOT / "src" / "buddy_agent", ROOT / "tests")
ALLOWED_FILES = {
    ROOT / "src" / "buddy_agent" / "ecosystem.py",
    ROOT / "src" / "buddy_agent" / "references.py",
}
LEGACY_TOKENS = ("hermes_agent", "hermes-agent", "openclaw", "OpenClaw")


def iter_text_files() -> list[Path]:
    """Return source files that should be Buddy-native."""
    files: list[Path] = []
    for base in CHECK_DIRS:
        if not base.exists():
            continue
        files.extend(path for path in base.rglob("*.py") if path not in ALLOWED_FILES)
    return sorted(files)


def find_legacy_tokens() -> list[str]:
    """Return formatted legacy token findings."""
    findings: list[str] = []
    for path in iter_text_files():
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for token in LEGACY_TOKENS:
                if token in line:
                    relative = path.relative_to(ROOT)
                    findings.append(f"{relative}:{line_number}: found {token!r}")
    return findings


def main() -> int:
    """Run the rebrand check."""
    findings = find_legacy_tokens()
    if not findings:
        print("Rebrand check: ok")
        return 0

    print("Rebrand check: found unexpected legacy naming")
    for finding in findings:
        print(f"- {finding}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
