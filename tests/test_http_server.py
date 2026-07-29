from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from buddy_agent.http_server import BridgeSettings, create_server
from buddy_agent.mcp_server import BuddyMcpConfig


def read_json(request: urllib.request.Request | str) -> dict[str, object]:
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def test_loopback_bridge_exposes_health_tools_and_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUDDY_PROVIDER", "disabled")
    config = BuddyMcpConfig(project_root=tmp_path, vault_root=None)
    server = create_server(BridgeSettings(port=0), config=config)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        health = read_json(f"{base}/health")
        assert health["ok"] is True
        assert health["runtime"]["protocol_version"] == "prismtek-buddy-game-v1"  # type: ignore[index]

        tools = read_json(f"{base}/v1/tools")
        names = {tool["name"] for tool in tools["tools"]}  # type: ignore[index,union-attr]
        assert "buddy.game.chat" in names
        assert "buddy.task.create" in names

        request = urllib.request.Request(
            f"{base}/v1/call",
            data=json.dumps({"tool": "buddy.game.status", "arguments": {}}).encode(),
            method="POST",
            headers={"content-type": "application/json", "origin": "https://prismtek.dev"},
        )
        called = read_json(request)
        assert called["ok"] is True
        assert called["result"]["provider"]["configured"] is False  # type: ignore[index]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_bridge_rejects_untrusted_browser_origin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BUDDY_PROVIDER", "disabled")
    server = create_server(
        BridgeSettings(port=0),
        config=BuddyMcpConfig(project_root=tmp_path, vault_root=None),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/health",
            headers={"origin": "https://evil.example"},
        )
        with pytest.raises(urllib.error.HTTPError) as failure:
            urllib.request.urlopen(request, timeout=5)
        assert failure.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_non_loopback_binding_requires_remote_opt_in_and_token(tmp_path: Path) -> None:
    config = BuddyMcpConfig(project_root=tmp_path, vault_root=None)
    with pytest.raises(RuntimeError, match="ALLOW_REMOTE"):
        create_server(BridgeSettings(host="0.0.0.0", port=0), config=config)
    with pytest.raises(RuntimeError, match="TOKEN"):
        create_server(
            BridgeSettings(host="0.0.0.0", port=0, allow_remote=True),
            config=config,
        )
