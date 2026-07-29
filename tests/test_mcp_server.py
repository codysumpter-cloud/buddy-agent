from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from buddy_agent.mcp_server import (
    BuddyMcpConfig,
    McpToolError,
    call_tool,
    handle_request,
    serve,
)


def config(tmp_path: Path) -> BuddyMcpConfig:
    project = tmp_path / "project"
    vault = tmp_path / "vault"
    project.mkdir()
    vault.mkdir()
    (project / "README.md").write_text("# Example\napi_key=secret-value\n", encoding="utf-8")
    (project / "AGENTS.md").write_text("Verify before claiming success.\n", encoding="utf-8")
    (vault / "Decision.md").write_text(
        "# Decision\nUse PostgreSQL for durable event storage. password=hunter2\n",
        encoding="utf-8",
    )
    private = vault / "00-Private"
    private.mkdir()
    (private / "Secret.md").write_text("PostgreSQL private secret", encoding="utf-8")
    return BuddyMcpConfig(project_root=project, vault_root=vault)


def test_initialize_lists_tools_and_self_test(tmp_path: Path) -> None:
    selected = config(tmp_path)
    initialized = handle_request(selected, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert initialized is not None
    assert initialized["result"]["serverInfo"]["name"] == "buddy-mcp"

    listed = handle_request(selected, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert listed is not None
    names = {tool["name"] for tool in listed["result"]["tools"]}
    assert {
        "buddy.self_test",
        "buddy.status",
        "buddy.project_context",
        "buddy.vault_search",
        "buddy.repo_overview",
        "buddy.codex_delegate",
    } <= names

    result = call_tool(selected, "buddy.self_test", {})
    assert result["ok"] is True
    assert result["safety"]["shell_execution"] is False


def test_project_context_is_allowlisted_and_redacted(tmp_path: Path) -> None:
    selected = config(tmp_path)
    result = call_tool(selected, "buddy.project_context", {"names": ["README.md", "AGENTS.md"]})
    assert [entry["name"] for entry in result["files"]] == ["README.md", "AGENTS.md"]
    assert "secret-value" not in json.dumps(result)
    assert "[REDACTED]" in result["files"][0]["content"]

    with pytest.raises(McpToolError):
        call_tool(selected, "buddy.project_context", {"names": [".env"]})


def test_vault_search_skips_private_paths_and_redacts(tmp_path: Path) -> None:
    selected = config(tmp_path)
    result = call_tool(selected, "buddy.vault_search", {"query": "PostgreSQL durable", "limit": 10})
    assert result["result_count"] == 1
    assert result["results"][0]["path"] == "Decision.md"
    payload = json.dumps(result)
    assert "hunter2" not in payload
    assert "00-Private" not in payload


def test_repo_overview_refuses_escape(tmp_path: Path) -> None:
    selected = config(tmp_path)
    result = call_tool(selected, "buddy.repo_overview", {})
    assert "README.md" in result["markers"]
    with pytest.raises(McpToolError):
        call_tool(selected, "buddy.repo_overview", {"path": "../"})


def test_codex_delegate_writes_reviewable_brief_without_launching(tmp_path: Path) -> None:
    selected = config(tmp_path)
    result = call_tool(
        selected,
        "buddy.codex_delegate",
        {
            "title": "Fix verification",
            "objective": "Run tests with access_token=do-not-leak and repair the failure.",
            "verification": ["pytest", "ruff check ."],
            "risk": "repo-mutation",
        },
    )
    path = selected.project_root / result["path"]
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "do-not-leak" not in body
    assert "[REDACTED]" in body
    assert result["launched_codex"] is False

    with pytest.raises(McpToolError):
        call_tool(
            selected,
            "buddy.codex_delegate",
            {"title": "Destroy", "objective": "Delete everything", "risk": "destructive"},
        )


def test_stdio_round_trip_and_safe_error(tmp_path: Path) -> None:
    selected = config(tmp_path)
    requests = "\n".join(
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "buddy.self_test", "arguments": {}},
                }
            ),
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "buddy.missing", "arguments": {}},
                }
            ),
        ]
    )
    output = io.StringIO()
    assert serve(io.StringIO(requests + "\n"), output, config=selected) == 0
    responses = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [response["id"] for response in responses] == [1, 2, 3]
    assert responses[1]["result"]["isError"] is False
    assert responses[2]["result"]["isError"] is True
