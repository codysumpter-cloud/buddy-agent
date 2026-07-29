"""Dependency-free, local-first MCP server for Buddy Agent.

The v1 server intentionally exposes a narrow tool surface. It never executes a
shell command, launches Codex, reads browser state, or follows paths outside the
configured project/vault roots.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from .metadata import PROJECT_NAME, VERSION

PROTOCOL_VERSION = "2025-06-18"
MAX_FILE_BYTES = 256_000
MAX_RESULTS = 20
PROJECT_CONTEXT_NAMES = (
    "AGENTS.md",
    "README.md",
    "SYSTEMMAP.md",
    "TASK_STATE.md",
    "WORK_IN_PROGRESS.md",
    "REVIEW.md",
)
BLOCKED_PARTS = {
    ".git",
    ".env",
    ".venv",
    "node_modules",
    "00-Private",
    "99-System/Security",
    "secrets",
}
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|private[_-]?key)\s*[:=]\s*([^\s]+)"
)
SAFE_SLUG = re.compile(r"[^a-z0-9]+")


class McpToolError(ValueError):
    """A safe, user-visible tool failure."""


@dataclass(frozen=True)
class BuddyMcpConfig:
    """Resolved local roots for one MCP process."""

    project_root: Path
    vault_root: Path | None

    @classmethod
    def from_env(cls) -> "BuddyMcpConfig":
        project = Path(os.getenv("BUDDY_PROJECT_ROOT", os.getcwd())).expanduser().resolve()
        raw_vault = os.getenv("BUDDY_VAULT_PATH", "").strip()
        vault = Path(raw_vault).expanduser().resolve() if raw_vault else None
        return cls(project_root=project, vault_root=vault)


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]

    def as_mcp(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


TOOLS = (
    ToolDefinition(
        "buddy.self_test",
        "Confirm the Buddy MCP executable, protocol, roots, and tool registry are healthy.",
        {"type": "object", "properties": {}, "additionalProperties": False},
    ),
    ToolDefinition(
        "buddy.status",
        "Return sanitized Buddy MCP runtime status.",
        {"type": "object", "properties": {}, "additionalProperties": False},
    ),
    ToolDefinition(
        "buddy.project_context",
        "Read allowlisted project context files from the configured repository root.",
        {
            "type": "object",
            "properties": {
                "names": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(PROJECT_CONTEXT_NAMES)},
                    "maxItems": len(PROJECT_CONTEXT_NAMES),
                }
            },
            "additionalProperties": False,
        },
    ),
    ToolDefinition(
        "buddy.vault_search",
        "Search public-safe Markdown notes under the configured KnowledgeVault root.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 1, "maxLength": 300},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_RESULTS},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    ),
    ToolDefinition(
        "buddy.repo_overview",
        "Inspect repository markers and branch metadata without executing shell commands.",
        {
            "type": "object",
            "properties": {"path": {"type": "string", "maxLength": 500}},
            "additionalProperties": False,
        },
    ),
    ToolDefinition(
        "buddy.codex_delegate",
        "Write a reviewable Codex delegation brief under .buddy/codex-delegations/.",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 120},
                "objective": {"type": "string", "minLength": 1, "maxLength": 12_000},
                "verification": {"type": "array", "items": {"type": "string", "maxLength": 500}, "maxItems": 20},
                "risk": {
                    "type": "string",
                    "enum": ["read-only", "draft-only", "write", "repo-mutation", "destructive"],
                },
            },
            "required": ["title", "objective"],
            "additionalProperties": False,
        },
    ),
)
TOOL_BY_NAME = {tool.name: tool for tool in TOOLS}


def _redact(text: str) -> str:
    return SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)


def _safe_relative(root: Path, candidate: Path) -> Path:
    resolved = candidate.expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise McpToolError("path is outside the configured root") from error
    if any(part in BLOCKED_PARTS or part.lower().endswith(".env") for part in resolved.parts):
        raise McpToolError("path is blocked by Buddy's local safety policy")
    return resolved


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise McpToolError(f"file does not exist: {path.name}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise McpToolError(f"file is larger than {MAX_FILE_BYTES} bytes: {path.name}")
    return _redact(path.read_text(encoding="utf-8", errors="replace"))


def _slug(value: str) -> str:
    slug = SAFE_SLUG.sub("-", value.lower()).strip("-")
    return slug[:60] or "delegation"


def _branch_name(root: Path) -> str | None:
    head = root / ".git" / "HEAD"
    if not head.is_file():
        return None
    value = head.read_text(encoding="utf-8", errors="replace").strip()
    prefix = "ref: refs/heads/"
    if value.startswith(prefix):
        return value[len(prefix) :]
    return f"detached:{value[:12]}" if value else "detached"


def _tool_self_test(config: BuddyMcpConfig, _arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "server": PROJECT_NAME,
        "version": VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "tool_count": len(TOOLS),
        "project_root_exists": config.project_root.is_dir(),
        "vault_configured": config.vault_root is not None,
        "safety": {
            "shell_execution": False,
            "browser_session_access": False,
            "arbitrary_path_access": False,
            "codex_auto_launch": False,
        },
    }


def _tool_status(config: BuddyMcpConfig, _arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "server": PROJECT_NAME,
        "version": VERSION,
        "transport": "stdio",
        "project_root": str(config.project_root),
        "project_root_exists": config.project_root.is_dir(),
        "vault_root": str(config.vault_root) if config.vault_root else None,
        "vault_root_exists": bool(config.vault_root and config.vault_root.is_dir()),
        "branch": _branch_name(config.project_root),
    }


def _tool_project_context(config: BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    requested = arguments.get("names") or list(PROJECT_CONTEXT_NAMES)
    if not isinstance(requested, list) or any(name not in PROJECT_CONTEXT_NAMES for name in requested):
        raise McpToolError("names must contain only allowlisted project context filenames")
    files: list[dict[str, Any]] = []
    for name in requested:
        path = _safe_relative(config.project_root, config.project_root / str(name))
        if not path.is_file():
            continue
        text = _read_text(path)
        files.append(
            {
                "name": name,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "content": text,
            }
        )
    return {"root": str(config.project_root), "files": files}


def _query_terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[a-z0-9_-]{2,}", query.lower()) if term]


def _tool_vault_search(config: BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    if config.vault_root is None or not config.vault_root.is_dir():
        raise McpToolError("BUDDY_VAULT_PATH is not configured to an existing directory")
    query = str(arguments.get("query", "")).strip()
    terms = _query_terms(query)
    if not terms:
        raise McpToolError("query must contain at least one searchable term")
    limit = int(arguments.get("limit", 8))
    limit = max(1, min(MAX_RESULTS, limit))
    matches: list[tuple[int, str, str]] = []
    for path in config.vault_root.rglob("*.md"):
        try:
            safe_path = _safe_relative(config.vault_root, path)
        except McpToolError:
            continue
        if safe_path.stat().st_size > MAX_FILE_BYTES:
            continue
        text = safe_path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if score <= 0:
            continue
        first = min((lowered.find(term) for term in terms if term in lowered), default=0)
        start = max(0, first - 180)
        end = min(len(text), first + 420)
        snippet = _redact(text[start:end].replace("\x00", " ").strip())
        relative = str(safe_path.relative_to(config.vault_root))
        matches.append((score, relative, snippet))
    matches.sort(key=lambda row: (-row[0], row[1]))
    return {
        "query": query,
        "results": [
            {"score": score, "path": path, "snippet": snippet}
            for score, path, snippet in matches[:limit]
        ],
        "result_count": min(len(matches), limit),
    }


def _tool_repo_overview(config: BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    raw_path = str(arguments.get("path", ".")).strip() or "."
    root = _safe_relative(config.project_root, config.project_root / raw_path)
    if not root.is_dir():
        raise McpToolError("repository path is not a directory")
    markers = [
        name
        for name in (
            "AGENTS.md",
            "README.md",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "project.godot",
            "Package.swift",
        )
        if (root / name).is_file()
    ]
    return {
        "path": str(root.relative_to(config.project_root)) or ".",
        "branch": _branch_name(root),
        "markers": markers,
        "has_git_metadata": (root / ".git").exists(),
        "buddy_directory": (root / ".buddy").is_dir(),
    }


def _tool_codex_delegate(config: BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    title = str(arguments.get("title", "")).strip()
    objective = str(arguments.get("objective", "")).strip()
    if not title or not objective:
        raise McpToolError("title and objective are required")
    risk = str(arguments.get("risk", "draft-only"))
    if risk in {"destructive"}:
        raise McpToolError("destructive delegation briefs are denied by default")
    verification = arguments.get("verification") or []
    if not isinstance(verification, list) or any(not isinstance(item, str) for item in verification):
        raise McpToolError("verification must be an array of strings")
    output_root = _safe_relative(
        config.project_root,
        config.project_root / ".buddy" / "codex-delegations",
    )
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _safe_relative(output_root, output_root / f"{stamp}-{_slug(title)}.md")
    checks = "\n".join(f"- `{_redact(item)}`" for item in verification) or "- Define and run the repository's required checks."
    body = (
        "# Codex Delegation Brief\n\n"
        f"- Created: `{datetime.now(UTC).isoformat()}`\n"
        f"- Risk: `{risk}`\n"
        "- Approval: required before external, destructive, paid, credential, or production actions\n\n"
        "## Objective\n\n"
        f"{_redact(objective)}\n\n"
        "## Verification\n\n"
        f"{checks}\n\n"
        "## Required handoff\n\n"
        "Report changed paths, checks run, evidence, remaining blockers, and rollback. "
        "Do not claim success without executable verification.\n"
    )
    path.write_text(body, encoding="utf-8")
    return {
        "created": True,
        "path": str(path.relative_to(config.project_root)),
        "sha256": hashlib.sha256(body.encode()).hexdigest(),
        "launched_codex": False,
    }


TOOL_HANDLERS = {
    "buddy.self_test": _tool_self_test,
    "buddy.status": _tool_status,
    "buddy.project_context": _tool_project_context,
    "buddy.vault_search": _tool_vault_search,
    "buddy.repo_overview": _tool_repo_overview,
    "buddy.codex_delegate": _tool_codex_delegate,
}


def call_tool(config: BuddyMcpConfig, name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
    """Call one registered tool with a JSON object argument."""
    if name not in TOOL_BY_NAME:
        raise McpToolError(f"unknown tool: {name}")
    payload = arguments or {}
    if not isinstance(payload, dict):
        raise McpToolError("tool arguments must be a JSON object")
    return TOOL_HANDLERS[name](config, payload)


def _success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_request(config: BuddyMcpConfig, request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one MCP JSON-RPC request."""
    request_id = request.get("id")
    method = request.get("method")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _success(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "buddy-mcp", "version": VERSION},
                "instructions": "Local-first Buddy tools. External actions remain approval-gated.",
            },
        )
    if method == "ping":
        return _success(request_id, {})
    if method == "tools/list":
        return _success(request_id, {"tools": [tool.as_mcp() for tool in TOOLS]})
    if method == "tools/call":
        params = request.get("params") or {}
        try:
            result = call_tool(config, str(params.get("name", "")), params.get("arguments"))
        except McpToolError as error:
            return _success(
                request_id,
                {
                    "content": [{"type": "text", "text": json.dumps({"ok": False, "error": str(error)})}],
                    "isError": True,
                },
            )
        return _success(
            request_id,
            {
                "content": [{"type": "text", "text": json.dumps(result, sort_keys=True)}],
                "structuredContent": result,
                "isError": False,
            },
        )
    return _error(request_id, -32601, f"method not found: {method}")


def serve(
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
    *,
    config: BuddyMcpConfig | None = None,
) -> int:
    """Serve newline-delimited MCP JSON-RPC on stdio until EOF."""
    selected = config or BuddyMcpConfig.from_env()
    for raw_line in input_stream:
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            if not isinstance(parsed, dict):
                raise ValueError("request must be a JSON object")
            response = handle_request(selected, parsed)
        except (json.JSONDecodeError, ValueError) as error:
            response = _error(None, -32700, f"invalid JSON-RPC request: {error}")
        except Exception:
            response = _error(None, -32603, "internal Buddy MCP error")
        if response is not None:
            output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
            output_stream.flush()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="buddy-mcp", description="Buddy Agent local stdio MCP server")
    parser.add_argument("--self-test", action="store_true", help="Run the executable self-test and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = BuddyMcpConfig.from_env()
    if args.self_test:
        print(json.dumps(_tool_self_test(config, {}), sort_keys=True))
        return 0
    return serve(config=config)


if __name__ == "__main__":
    raise SystemExit(main())
