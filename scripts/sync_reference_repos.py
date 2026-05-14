#!/usr/bin/env python3
"""Clone or update Buddy Agent reference repositories locally.

This script writes into `reference_repos/`, which is ignored by git. It does not
vendor source into Buddy Agent. Use it to inspect, audit, diff, and port small
pieces behind native Buddy Agent boundaries.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from buddy_agent.references import REFERENCE_REPOS, ReferenceRepo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEST = ROOT / "reference_repos"


def run(command: list[str], *, cwd: Path | None = None, dry_run: bool = False) -> None:
    """Run a command, or print it during dry-run mode."""
    prefix = f"cd {cwd} && " if cwd else ""
    printable = " ".join(command)
    if dry_run:
        print(f"DRY RUN: {prefix}{printable}")
        return
    subprocess.run(command, cwd=cwd, check=True)


def repo_dir(destination: Path, repo: ReferenceRepo) -> Path:
    """Return the local directory for a reference repo."""
    return destination / repo.repository.replace("/", "__")


def sync_repo(destination: Path, repo: ReferenceRepo, *, dry_run: bool = False) -> None:
    """Clone or update one reference repo."""
    target = repo_dir(destination, repo)
    if target.exists():
        print(f"Updating {repo.repository}")
        run(["git", "fetch", "--all", "--prune"], cwd=target, dry_run=dry_run)
        run(["git", "checkout", repo.default_branch], cwd=target, dry_run=dry_run)
        run(["git", "pull", "--ff-only"], cwd=target, dry_run=dry_run)
        return

    print(f"Cloning {repo.repository}")
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
    run(
        [
            "git",
            "clone",
            "--branch",
            repo.default_branch,
            "--depth",
            "1",
            repo.clone_url,
            str(target),
        ],
        dry_run=dry_run,
    )


def write_report(destination: Path) -> Path:
    """Write a lightweight local report of synced repos."""
    report = destination / "REFERENCE_REPOS.md"
    lines = ["# Synced Reference Repositories", ""]
    for repo in REFERENCE_REPOS:
        target = repo_dir(destination, repo)
        status = "present" if target.exists() else "missing"
        lines.append(f"- `{repo.repository}` - {repo.role} - {status}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    """Run the reference sync command."""
    parser = argparse.ArgumentParser(description="Sync Buddy Agent reference repositories locally.")
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for repo in REFERENCE_REPOS:
        sync_repo(args.dest, repo, dry_run=args.dry_run)

    if not args.dry_run:
        report = write_report(args.dest)
        print(f"Wrote {report}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
