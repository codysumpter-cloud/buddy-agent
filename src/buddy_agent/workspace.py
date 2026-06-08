"""Permissioned Buddy playground workspace primitives.

This module gives Buddy a local workspace for creating files, code notes, art prompts,
browser research notes, and user-reviewable drafts. It intentionally does not send email,
create calendar events, post messages, browse the web, launch apps, or touch connected
accounts. Those actions belong behind explicit user approval and audited adapters.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

WorkspaceItemKind = Literal[
    "email",
    "message",
    "calendar",
    "art",
    "browser",
    "code",
    "file",
]

PLAYGROUND_RELATIVE_PATH = Path(".buddy") / "playground"

PASSIVE_CAPABILITIES = (
    "local_file_creation",
    "code_writing",
    "art_request_generation",
    "browser_research_planning",
    "email_draft_generation",
    "message_draft_generation",
    "calendar_draft_generation",
    "receipt_logging",
)

REQUIRES_APPROVAL = (
    "send_email",
    "send_message",
    "create_calendar_event",
    "post_to_web",
    "open_browser_session",
    "modify_external_account",
    "delete_or_overwrite_user_files",
    "purchase_or_transfer_money",
)

WORKSPACE_DIRECTORIES = (
    Path("files"),
    Path("code"),
    Path("code") / "tasks",
    Path("art"),
    Path("art") / "requests",
    Path("browser"),
    Path("browser") / "research_notes",
    Path("outbox"),
    Path("outbox") / "email_drafts",
    Path("outbox") / "message_drafts",
    Path("outbox") / "calendar_drafts",
    Path("receipts"),
)


@dataclass(frozen=True)
class WorkspaceInitResult:
    """Summary for initializing a Buddy playground."""

    root: Path
    workspace: Path
    files_written: tuple[Path, ...]
    files_skipped: tuple[Path, ...]
    directories_created: tuple[Path, ...]

    def summary_lines(self) -> tuple[str, ...]:
        """Return CLI-friendly summary lines."""

        lines = [
            f"ok workspace: initialized Buddy playground at {self.workspace}",
            f"directories={len(self.directories_created)}",
            f"files_written={len(self.files_written)}",
            f"files_skipped={len(self.files_skipped)}",
        ]
        lines.extend(f"dir {path}" for path in self.directories_created)
        lines.extend(f"wrote {path}" for path in self.files_written)
        lines.extend(f"skipped existing {path}" for path in self.files_skipped)
        return tuple(lines)


@dataclass(frozen=True)
class WorkspaceItemResult:
    """A created workspace item."""

    kind: WorkspaceItemKind
    path: Path
    requires_approval: bool

    def summary_lines(self) -> tuple[str, ...]:
        """Return CLI-friendly summary lines."""

        approval = "required" if self.requires_approval else "not_required"
        return (
            f"ok workspace: created {self.kind} item at {self.path}",
            f"approval={approval}",
        )


@dataclass(frozen=True)
class WorkspaceStatus:
    """Status summary for an existing Buddy playground."""

    root: Path
    workspace: Path
    exists: bool
    item_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe status object."""

        return {
            "root": str(self.root),
            "workspace": str(self.workspace),
            "exists": self.exists,
            "item_counts": self.item_counts,
            "passive_capabilities": list(PASSIVE_CAPABILITIES),
            "requires_approval": list(REQUIRES_APPROVAL),
        }

    def to_json(self) -> str:
        """Return pretty JSON."""

        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def playground_path(root: Path | str = ".") -> Path:
    """Return the Buddy playground path for a project root."""

    return Path(root).expanduser().resolve() / PLAYGROUND_RELATIVE_PATH


def init_buddy_workspace(root: Path | str = ".", *, overwrite: bool = False) -> WorkspaceInitResult:
    """Create a local Buddy playground workspace under `.buddy/playground`."""

    root_path = Path(root).expanduser().resolve()
    workspace = playground_path(root_path)
    directories_created: list[Path] = []

    for relative_directory in WORKSPACE_DIRECTORIES:
        directory = workspace / relative_directory
        directory.mkdir(parents=True, exist_ok=True)
        directories_created.append(directory)

    files_written: list[Path] = []
    files_skipped: list[Path] = []

    for relative_path, content in _workspace_templates().items():
        destination = workspace / relative_path
        if destination.exists() and not overwrite:
            files_skipped.append(destination)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        files_written.append(destination)

    return WorkspaceInitResult(
        root=root_path,
        workspace=workspace,
        files_written=tuple(files_written),
        files_skipped=tuple(files_skipped),
        directories_created=tuple(directories_created),
    )


def workspace_status(root: Path | str = ".") -> WorkspaceStatus:
    """Return status and item counts for the Buddy playground."""

    root_path = Path(root).expanduser().resolve()
    workspace = playground_path(root_path)
    counts: dict[str, int] = {}

    for kind, directory in _item_directories().items():
        item_directory = workspace / directory
        counts[kind] = _count_files(item_directory)

    return WorkspaceStatus(
        root=root_path,
        workspace=workspace,
        exists=workspace.exists(),
        item_counts=counts,
    )


def write_workspace_item(
    root: Path | str,
    *,
    kind: WorkspaceItemKind,
    title: str,
    body: str,
) -> WorkspaceItemResult:
    """Write a user-reviewable workspace item."""

    if kind not in _item_directories():
        raise ValueError(f"unsupported workspace item kind: {kind}")

    workspace = playground_path(root)
    directory = workspace / _item_directories()[kind]
    directory.mkdir(parents=True, exist_ok=True)

    stem = _next_item_stem(directory, kind, title)
    suffix = ".json" if kind == "calendar" else ".md"
    destination = directory / f"{stem}{suffix}"
    destination.write_text(_render_item(kind, title, body), encoding="utf-8")

    return WorkspaceItemResult(
        kind=kind,
        path=destination,
        requires_approval=kind in {"email", "message", "calendar"},
    )


def _workspace_templates() -> dict[Path, str]:
    manifest = {
        "name": "Buddy Playground",
        "schema_version": 1,
        "mode": "local_reviewable_workspace",
        "passive_capabilities": list(PASSIVE_CAPABILITIES),
        "requires_user_approval": list(REQUIRES_APPROVAL),
        "default_policy": {
            "network": "disabled_by_default",
            "external_accounts": "draft_only_without_adapter_approval",
            "file_scope": ".buddy/playground plus explicit project files",
            "destructive_actions": "deny_by_default",
        },
    }
    permissions = {
        "allow": list(PASSIVE_CAPABILITIES),
        "require_confirmation": list(REQUIRES_APPROVAL),
        "deny_by_default": [
            "secret_extraction",
            "credential_inventory",
            "wallet_signing",
            "financial_transfer",
            "unreviewed_external_send",
        ],
    }
    return {
        Path("README.md"): _workspace_readme(),
        Path("manifest.json"): _json(manifest),
        Path("permissions.json"): _json(permissions),
        Path("browser") / "README.md": _browser_readme(),
        Path("outbox") / "README.md": _outbox_readme(),
        Path("art") / "README.md": _art_readme(),
        Path("code") / "README.md": _code_readme(),
        Path("files") / "README.md": _files_readme(),
    }


def _workspace_readme() -> str:
    return (
        "# Buddy Playground\n\n"
        "This is Buddy's local, reviewable workspace. Buddy can draft, plan, write, "
        "index, and create files here without touching external accounts.\n\n"
        "## What Buddy can do here\n\n"
        "- create local files\n"
        "- write and organize code tasks\n"
        "- generate art prompts and asset briefs\n"
        "- create browser/research notes for a future web surface\n"
        "- draft emails, messages, and calendar events for user review\n"
        "- record receipts and task context\n\n"
        "## What still needs approval\n\n"
        "Sending email, sending messages, creating real calendar events, browsing logged-in "
        "sessions, posting online, purchases, money movement, destructive file changes, and "
        "external account mutations require explicit user approval through audited adapters.\n"
    )


def _browser_readme() -> str:
    return (
        "# Browser Playground\n\n"
        "Use this folder for browser plans, research notes, bookmarks, web app sketches, "
        "and future browser-surface specs. No browser session is launched by this workspace.\n"
    )


def _outbox_readme() -> str:
    return (
        "# Outbox\n\n"
        "Drafts live here until the user reviews and approves them. Draft files are not sent, "
        "posted, or synced by this workspace.\n"
    )


def _art_readme() -> str:
    return (
        "# Art Requests\n\n"
        "Use this folder for image prompts, sprite briefs, style guides, asset manifests, "
        "and generation receipts.\n"
    )


def _code_readme() -> str:
    return (
        "# Code Playground\n\n"
        "Use this folder for code tasks, snippets, generated modules, refactor plans, and "
        "implementation notes before applying changes to the main project.\n"
    )


def _files_readme() -> str:
    return (
        "# Files\n\n"
        "Buddy can place generated local files here before they are copied into the project "
        "or attached to another workflow.\n"
    )


def _item_directories() -> dict[WorkspaceItemKind, Path]:
    return {
        "email": Path("outbox") / "email_drafts",
        "message": Path("outbox") / "message_drafts",
        "calendar": Path("outbox") / "calendar_drafts",
        "art": Path("art") / "requests",
        "browser": Path("browser") / "research_notes",
        "code": Path("code") / "tasks",
        "file": Path("files"),
    }


def _render_item(kind: WorkspaceItemKind, title: str, body: str) -> str:
    if kind == "calendar":
        payload = {
            "kind": "calendar_draft",
            "status": "draft_requires_user_approval",
            "title": title,
            "body": body,
        }
        return _json(payload)

    approval = "yes" if kind in {"email", "message"} else "no"
    return (
        f"# {title}\n\n"
        f"kind: {kind}\n"
        "status: draft\n"
        f"requires_user_approval: {approval}\n\n"
        "---\n\n"
        f"{body.strip()}\n"
    )


def _next_item_stem(directory: Path, kind: WorkspaceItemKind, title: str) -> str:
    prefix = f"{kind}_"
    existing = [path for path in directory.iterdir() if path.is_file() and path.name.startswith(prefix)]
    return f"{prefix}{len(existing) + 1:04d}_{_slugify(title)}"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "untitled"


def _count_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(1 for path in directory.iterdir() if path.is_file())


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"
