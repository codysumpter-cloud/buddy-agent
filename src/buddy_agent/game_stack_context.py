"""Bounded cross-stack context for Buddy inside Prismtek games."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from . import mcp_server as base
from .game_protocol import JSONValue, normalize_context

POLICY_FILES = ("AGENTS.md", "REVIEW.md", "SYSTEMMAP.md", "TASK_STATE.md")
MAX_POLICY_FILE_CHARS = 4_000
MAX_POLICY_TOTAL_CHARS = 12_000
MAX_BRAIN_REPORT_BYTES = 64_000
MAX_VAULT_RESULTS = 4


@dataclass(frozen=True)
class GameStackReceipt:
    """Public-safe evidence of which stack layers informed one game response."""

    buap_policy_files: tuple[str, ...]
    buap_policy_hashes: dict[str, str]
    knowledge_vault_configured: bool
    knowledge_vault_result_count: int
    buddy_brain_report_configured: bool
    buddy_brain_report_loaded: bool
    omni_buddy_transport_contract: bool
    omni_buddy_endpoint_configured: bool

    def to_dict(self) -> dict[str, object]:
        return cast(dict[str, object], asdict(self))


def _policy_context(config: base.BuddyMcpConfig) -> tuple[list[JSONValue], dict[str, str]]:
    try:
        payload = base.call_tool(
            config,
            "buddy.project_context",
            {"names": list(POLICY_FILES)},
        )
    except base.McpToolError:
        return [], {}
    raw_files = payload.get("files", [])
    if not isinstance(raw_files, list):
        return [], {}
    files: list[JSONValue] = []
    hashes: dict[str, str] = {}
    remaining = MAX_POLICY_TOTAL_CHARS
    for raw_file in raw_files:
        if remaining <= 0 or not isinstance(raw_file, dict):
            break
        name = raw_file.get("name")
        sha256 = raw_file.get("sha256")
        content = raw_file.get("content")
        if not isinstance(name, str) or not isinstance(content, str):
            continue
        bounded = content[: min(MAX_POLICY_FILE_CHARS, remaining)]
        remaining -= len(bounded)
        item: dict[str, JSONValue] = {"name": name, "content": bounded}
        if isinstance(sha256, str):
            item["sha256"] = sha256
            hashes[name] = sha256
        files.append(item)
    return files, hashes


def _vault_context(config: base.BuddyMcpConfig, message: str) -> list[JSONValue]:
    if config.vault_root is None or not config.vault_root.is_dir():
        return []
    try:
        payload = base.call_tool(
            config,
            "buddy.vault_search",
            {"query": message[:300], "limit": MAX_VAULT_RESULTS},
        )
    except base.McpToolError:
        return []
    raw_results = payload.get("results", [])
    if not isinstance(raw_results, list):
        return []
    results: list[JSONValue] = []
    for raw_result in raw_results[:MAX_VAULT_RESULTS]:
        if not isinstance(raw_result, dict):
            continue
        path = raw_result.get("path")
        snippet = raw_result.get("snippet")
        score = raw_result.get("score")
        if not isinstance(path, str) or not isinstance(snippet, str):
            continue
        result: dict[str, JSONValue] = {
            "source": path,
            "snippet": snippet[:800],
        }
        if isinstance(score, int | float):
            result["score"] = score
        results.append(result)
    return results


def _brain_report() -> tuple[dict[str, JSONValue], bool, bool]:
    raw_path = os.getenv("BUDDY_BRAIN_REPORT_PATH", "").strip()
    if not raw_path:
        return {}, False, False
    path = Path(raw_path).expanduser()
    if not path.is_file() or path.stat().st_size > MAX_BRAIN_REPORT_BYTES:
        return {}, True, False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}, True, False
    if not isinstance(payload, dict):
        return {}, True, False
    return normalize_context(payload), True, True


def assemble_game_stack_context(
    config: base.BuddyMcpConfig,
    message: str,
) -> tuple[dict[str, JSONValue], GameStackReceipt]:
    """Collect policy, public-safe memory, and optional governance context."""
    policy, policy_hashes = _policy_context(config)
    evidence = _vault_context(config, message)
    brain_report, brain_configured, brain_loaded = _brain_report()
    omni_endpoint = os.getenv("BUDDY_OMNI_ENDPOINT", "").strip()
    context: dict[str, JSONValue] = {
        "buap_policy": policy,
        "knowledge_vault_evidence": evidence,
        "buddy_brain_report": brain_report,
        "transport_contracts": {
            "omni_buddy": "prismtek.buddy-game.v1",
            "omni_endpoint_configured": bool(omni_endpoint),
        },
        "instructions": (
            "Treat BUAP policy as binding. Treat KnowledgeVault snippets as evidence, "
            "not unquestionable truth. Use Buddy Brain metrics as governance context only."
        ),
    }
    receipt = GameStackReceipt(
        buap_policy_files=tuple(
            str(item.get("name"))
            for item in policy
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ),
        buap_policy_hashes=policy_hashes,
        knowledge_vault_configured=bool(config.vault_root and config.vault_root.is_dir()),
        knowledge_vault_result_count=len(evidence),
        buddy_brain_report_configured=brain_configured,
        buddy_brain_report_loaded=brain_loaded,
        omni_buddy_transport_contract=True,
        omni_buddy_endpoint_configured=bool(omni_endpoint),
    )
    return context, receipt
