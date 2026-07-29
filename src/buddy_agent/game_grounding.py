"""Bounded BUAP and KnowledgeVault grounding for Buddy game conversations."""

from __future__ import annotations

from typing import Any

from . import mcp_server

POLICY_CONTEXT_NAMES = (
    "AGENTS.md",
    "REVIEW.md",
    "SYSTEMMAP.md",
    "TASK_STATE.md",
    "WORK_IN_PROGRESS.md",
)
MAX_POLICY_FILES = 5
MAX_POLICY_EXCERPT = 2_000
MAX_MEMORY_RESULTS = 4
MAX_MEMORY_SNIPPET = 900


def _bounded_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return value.replace("\x00", " ").strip()[:limit]


def build_game_grounding(
    config: mcp_server.BuddyMcpConfig,
    message: str,
) -> dict[str, Any]:
    """Collect bounded policy and public-safe evidence without leaking local roots.

    Project policy is authoritative instruction context. KnowledgeVault matches are
    evidence only: the model is explicitly told not to execute instructions found
    inside retrieved notes.
    """

    policy_files: list[dict[str, Any]] = []
    try:
        context = mcp_server._tool_project_context(  # noqa: SLF001
            config,
            {"names": list(POLICY_CONTEXT_NAMES)},
        )
    except (mcp_server.McpToolError, OSError):
        context = {"files": []}

    raw_files = context.get("files", [])
    if isinstance(raw_files, list):
        for raw_file in raw_files[:MAX_POLICY_FILES]:
            if not isinstance(raw_file, dict):
                continue
            name = _bounded_text(raw_file.get("name"), 80)
            sha256 = _bounded_text(raw_file.get("sha256"), 64)
            excerpt = _bounded_text(raw_file.get("content"), MAX_POLICY_EXCERPT)
            if not name or not excerpt:
                continue
            policy_files.append(
                {
                    "name": name,
                    "sha256": sha256,
                    "excerpt": excerpt,
                }
            )

    memory_results: list[dict[str, Any]] = []
    if config.vault_root is not None and config.vault_root.is_dir():
        try:
            memory = mcp_server._tool_vault_search(  # noqa: SLF001
                config,
                {"query": message[:300], "limit": MAX_MEMORY_RESULTS},
            )
        except (mcp_server.McpToolError, OSError):
            memory = {"results": []}
        raw_results = memory.get("results", [])
        if isinstance(raw_results, list):
            for raw_result in raw_results[:MAX_MEMORY_RESULTS]:
                if not isinstance(raw_result, dict):
                    continue
                path = _bounded_text(raw_result.get("path"), 300)
                snippet = _bounded_text(raw_result.get("snippet"), MAX_MEMORY_SNIPPET)
                score = raw_result.get("score", 0)
                if not isinstance(score, int):
                    score = 0
                if not path or not snippet:
                    continue
                memory_results.append(
                    {
                        "path": path,
                        "score": score,
                        "snippet": snippet,
                    }
                )

    return {
        "policy_files": policy_files,
        "memory_results": memory_results,
        "claims": {
            "policy_is_instruction": True,
            "memory_is_evidence_not_instruction": True,
            "raw_private_content_excluded": True,
            "local_roots_excluded": True,
        },
    }


def grounding_metadata(grounding: dict[str, Any]) -> dict[str, Any]:
    """Return provenance metadata suitable for the game client, without excerpts."""

    policy: list[dict[str, Any]] = []
    raw_policy = grounding.get("policy_files", [])
    if isinstance(raw_policy, list):
        for raw_file in raw_policy:
            if not isinstance(raw_file, dict):
                continue
            policy.append(
                {
                    "name": _bounded_text(raw_file.get("name"), 80),
                    "sha256": _bounded_text(raw_file.get("sha256"), 64),
                }
            )

    memory: list[dict[str, Any]] = []
    raw_memory = grounding.get("memory_results", [])
    if isinstance(raw_memory, list):
        for raw_result in raw_memory:
            if not isinstance(raw_result, dict):
                continue
            score = raw_result.get("score", 0)
            memory.append(
                {
                    "path": _bounded_text(raw_result.get("path"), 300),
                    "score": score if isinstance(score, int) else 0,
                }
            )

    claims = grounding.get("claims", {})
    return {
        "policy_files": policy,
        "memory_results": memory,
        "policy_file_count": len(policy),
        "memory_result_count": len(memory),
        "claims": claims if isinstance(claims, dict) else {},
    }
