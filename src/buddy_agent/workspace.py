"""Local Buddy Playground workspace helpers.

The playground is a project-local review surface for files, code tasks, art requests,
browser notes, message/email/calendar drafts, and receipts. It does not send, post,
browse, mutate connected accounts, or create real calendar events.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

WorkspaceItemKind = Literal["email", "message", "calendar", "art", "browser", "code", "file"]

PLAYGROUND_RELATIVE_PATH = Path(".buddy") / "playground"

PASSIVE_CAPABILITIES: tuple[str, ...] = (
    "local_file_creation",
    "code_writing",
    "art_request_generation",
    "browser_research_planning",
    "email_draft_generation",
    "message_draft_generation",
    "calendar_draft_generation",
    "receipt_logging",
)

REQUIRES_APPROVAL: tuple[str, ...] = (
    "send_email",
    "send_message",
    "create_calendar_event",
    "post_to_web",
    "open_browser_session",
    "modify_external_account",
    "delete_or_overwrite_user_files",
    "purchase_or_transfer_money",
)

WORKSPACE_DIRECTORIES: tuple[Path, ...] = (
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

ITEM_DIRECTORIES: dict[WorkspaceItemKind, Path] = {
    "email": Path("outbox") / "email_drafts",
    "message": Path("outbox") / "message_drafts",
    "calendar": Path("outbox") / "calendar_drafts",
    "art": Path("art") / "requests",
    "browser": Path("browser") / "research_notes",
    "code": Path("code") / "tasks",
    "file": Path("files"),
}


@dataclass(frozen=True)
class WorkspaceInitResult:
    """Result of initializing the local playground."""

    root: Path
    workspace: Path
    directories_created: tuple[Path, ...]
    files_written: tuple[Path, ...]
    files_skipped: tuple[Path, ...]

    def summary_lines(self) -> tuple[str, ...]:
        """Return CLI-friendly summary lines."""

        lines = [
            f"ok workspace: initialized {self.workspace}",
            f"directories={len(self.directories_created)}",
            f"files_written={len(self.files_written)}",
            f"files_skipped={len(self.files_skipped)}",
        ]
        lines.extend(f"wrote {path}" for path in self.files_written)
        lines.extend(f"skipped existing {path}" for path in self.files_skipped)
        return tuple(lines)


@dataclass(frozen=True)
class WorkspaceItemResult:
    """Result of writing a playground item."""

    kind: WorkspaceItemKind
    path: Path
    requires_approval: bool

    def summary_lines(self) -> tuple[str, ...]:
        """Return CLI-friendly summary lines."""

        approval = "yes" if self.requires_approval else "no"
        return (
            f"ok workspace-item: kind={self.kind}",
            f"path={self.path}",
            f"requires_user_approval={approval}",
        )


@dataclass(frozen=True)
class WorkspaceStatus:
    """Current playground status."""

    root: Path
    workspace: Path
    exists: bool
    item_counts: dict[WorkspaceItemKind, int]

    def summary_lines(self) -> tuple[str, ...]:
        """Return CLI-friendly summary lines."""

        lines = [
            f"workspace={self.workspace}",
            f"exists={'yes' if self.exists else 'no'}",
        ]
        lines.extend(f"{kind}={self.item_counts[kind]}" for kind in ITEM_DIRECTORIES)
        return tuple(lines)


def parse_workspace_item_kind(value: str) -> WorkspaceItemKind:
    """Parse a user supplied item kind."""

    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"draft-email", "email"}:
        return "email"
    if normalized in {"draft-message", "message"}:
        return "message"
    if normalized in {"draft-calendar", "calendar", "event"}:
        return "calendar"
    if normalized in {"art-request", "art", "image"}:
        return "art"
    if normalized in {"browser-note", "browser", "research"}:
        return "browser"
    if normalized in {"code-task", "code"}:
        return "code"
    if normalized in {"file-note", "file", "note"}:
        return "file"
    raise ValueError(f"unsupported workspace item kind: {value!r}")


def playground_path(root: Path | str = ".") -> Path:
    """Return the playground path for a project root."""

    return Path(root).expanduser().resolve() / PLAYGROUND_RELATIVE_PATH


def init_buddy_workspace(root: Path | str = ".", *, overwrite: bool = False) -> WorkspaceInitResult:
    """Create the project-local Buddy Playground workspace."""

    root_path = Path(root).expanduser().resolve()
    workspace = playground_path(root_path)

    directories_created: list[Path] = []
    files_written: list[Path] = []
    files_skipped: list[Path] = []

    for relative_directory in WORKSPACE_DIRECTORIES:
        destination = workspace / relative_directory
        destination.mkdir(parents=True, exist_ok=True)
        directories_created.append(destination)

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
        directories_created=tuple(directories_created),
        files_written=tuple(files_written),
        files_skipped=tuple(files_skipped),
    )


def workspace_status(root: Path | str = ".") -> WorkspaceStatus:
    """Return current playground status."""

    root_path = Path(root).expanduser().resolve()
    workspace = playground_path(root_path)
    exists = workspace.exists()
    counts: dict[WorkspaceItemKind, int] = {}
    for kind, directory in ITEM_DIRECTORIES.items():
        target = workspace / directory
        counts[kind] = len([path for path in target.glob("*") if path.is_file()]) if target.exists() else 0
    return WorkspaceStatus(root=root_path, workspace=workspace, exists=exists, item_counts=counts)


def write_workspace_item(
    root: Path | str,
    *,
    kind: WorkspaceItemKind,
    title: str,
    body: str,
) -> WorkspaceItemResult:
    """Write a reviewable local workspace item."""

    init_buddy_workspace(root)
    workspace = playground_path(root)
    directory = workspace / ITEM_DIRECTORIES[kind]
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    slug = _slug(title)
    requires_approval = kind in {"email", "message", "calendar"}

    if kind == "calendar":
        path = directory / f"{timestamp}-{slug}.json"
        payload = {
            "title": title,
            "body": body,
            "kind": kind,
            "created_at": timestamp,
            "requires_user_approval": requires_approval,
            "status": "draft",
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path = directory / f"{timestamp}-{slug}.md"
        approval = "yes" if requires_approval else "no"
        path.write_text(
            "---\n"
            f"kind: {kind}\n"
            f"title: {title}\n"
            f"created_at: {timestamp}\n"
            f"requires_user_approval: {approval}\n"
            "status: draft\n"
            "---\n\n"
            f"# {title}\n\n{body.strip()}\n",
            encoding="utf-8",
        )

    return WorkspaceItemResult(kind=kind, path=path, requires_approval=requires_approval)


def _workspace_templates() -> dict[Path, str]:
    manifest = {
        "name": "Buddy Playground",
        "mode": "local_reviewable_workspace",
        "passive_capabilities": list(PASSIVE_CAPABILITIES),
        "requires_user_approval": list(REQUIRES_APPROVAL),
    }
    permissions = {
        "allowed_without_approval": list(PASSIVE_CAPABILITIES),
        "approval_required": list(REQUIRES_APPROVAL),
        "default_external_action": "deny_until_approved",
    }
    return {
        Path("README.md"): _workspace_readme(),
        Path("manifest.json"): json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        Path("permissions.json"): json.dumps(permissions, indent=2, sort_keys=True) + "\n",
        Path("browser") / "README.md": _sub_readme("Browser notes", "Store research plans, URLs, and secret-free receipts."),
        Path("outbox") / "README.md": _sub_readme("Outbox drafts", "Draft email, message, and calendar items for review before sending or creating."),
        Path("art") / "README.md": _sub_readme("Art requests", "Store image and sprite generation briefs."),
        Path("code") / "README.md": _sub_readme("Code tasks", "Store implementation plans and reviewable coding tasks."),
        Path("files") / "README.md": _sub_readme("Files", "Store local notes and generated files."),
    }


def _workspace_readme() -> str:
    return """# Buddy Playground

Buddy Playground is a local, reviewable workspace for Buddy and Lil' Buddy.

Buddy can create local files, code tasks, art prompts, browser/research notes, and draft emails/messages/calendar events here.

External actions still require approval: sending, posting, creating real calendar events, opening signed-in browser sessions, purchases, money movement, destructive changes, and external account mutations.
"""


def _sub_readme(title: str, body: str) -> str:
    return f"# {title}\n\n{body}\n"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"
