"""Loopback-first HTTP bridge for Buddy-enabled native and Web games."""

from __future__ import annotations

import argparse
import hmac
import json
import os
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
from typing import Any, cast
from urllib.parse import urlparse

from . import mcp_server
from .mcp_events import register_task_event_hooks
from .mcp_game import register_game_tools
from .mcp_tasks import register_task_tools

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_REQUEST_BYTES = 65_536
DEFAULT_ALLOWED_ORIGINS = (
    "https://prismtek.dev",
    "https://www.prismtek.dev",
    "https://app.prismtek.dev",
    "null",
)


@dataclass(frozen=True)
class BridgeSettings:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    token: str | None = None
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS
    allow_remote: bool = False
    max_request_bytes: int = MAX_REQUEST_BYTES

    @classmethod
    def from_env(cls, *, host: str | None = None, port: int | None = None) -> "BridgeSettings":
        raw_origins = os.getenv("BUDDY_HTTP_ALLOWED_ORIGINS", "").strip()
        origins = (
            tuple(item.strip() for item in raw_origins.split(",") if item.strip())
            if raw_origins
            else DEFAULT_ALLOWED_ORIGINS
        )
        return cls(
            host=host or os.getenv("BUDDY_HTTP_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST,
            port=port or int(os.getenv("BUDDY_HTTP_PORT", str(DEFAULT_PORT))),
            token=os.getenv("BUDDY_HTTP_TOKEN", "").strip() or None,
            allowed_origins=origins,
            allow_remote=os.getenv("BUDDY_HTTP_ALLOW_REMOTE", "").strip().lower()
            in {"1", "true", "yes"},
        )


def _is_loopback_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False


def _origin_allowed(origin: str | None, allowed: tuple[str, ...]) -> bool:
    if not origin:
        return True
    if origin in allowed:
        return True
    parsed = urlparse(origin)
    return parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}


def _register_runtime() -> None:
    register_task_tools()
    register_task_event_hooks()
    register_game_tools()


class BuddyHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        config: mcp_server.BuddyMcpConfig,
        settings: BridgeSettings,
    ) -> None:
        self.buddy_config = config
        self.buddy_settings = settings
        super().__init__(server_address, BuddyRequestHandler)


class BuddyRequestHandler(BaseHTTPRequestHandler):
    server_version = "BuddyHTTP/0.1"

    def log_message(self, format: str, *args: object) -> None:
        if os.getenv("BUDDY_HTTP_QUIET", "").strip().lower() not in {"1", "true", "yes"}:
            super().log_message(format, *args)

    def _runtime(self) -> BuddyHTTPServer:
        return cast(BuddyHTTPServer, self.server)

    def _origin(self) -> str | None:
        return self.headers.get("Origin")

    def _cors(self) -> dict[str, str]:
        origin = self._origin()
        headers = {
            "Cache-Control": "no-store",
            "Access-Control-Allow-Private-Network": "true",
            "Vary": "Origin",
        }
        if origin and _origin_allowed(origin, self._runtime().buddy_settings.allowed_origins):
            headers["Access-Control-Allow-Origin"] = origin
        return headers

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        for name, value in self._cors().items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def _preflight_ok(self) -> bool:
        origin = self._origin()
        if not _origin_allowed(origin, self._runtime().buddy_settings.allowed_origins):
            self._send(403, {"ok": False, "error": "origin is not allowed"})
            return False
        return True

    def _authorized(self) -> bool:
        expected = self._runtime().buddy_settings.token
        if expected is None:
            return True
        supplied = self.headers.get("Authorization", "")
        prefix = "Bearer "
        return supplied.startswith(prefix) and hmac.compare_digest(supplied[len(prefix) :], expected)

    def _require_access(self) -> bool:
        if not self._preflight_ok():
            return False
        if not self._authorized():
            self._send(401, {"ok": False, "error": "authorization required"})
            return False
        return True

    def do_OPTIONS(self) -> None:
        if not self._preflight_ok():
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        for name, value in self._cors().items():
            self.send_header(name, value)
        self.end_headers()

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        if not self._require_access():
            return
        try:
            if self.path in {"/", "/health"}:
                status = mcp_server.call_tool(
                    self._runtime().buddy_config,
                    "buddy.game.status",
                    {},
                )
                self._send(
                    200,
                    {
                        "ok": True,
                        "bridge": {
                            "transport": "http",
                            "host": self._runtime().buddy_settings.host,
                            "port": self._runtime().server_port,
                            "remote_enabled": self._runtime().buddy_settings.allow_remote,
                            "token_required": self._runtime().buddy_settings.token is not None,
                        },
                        "runtime": status,
                    },
                )
                return
            if self.path == "/v1/tools":
                self._send(200, {"ok": True, "tools": [tool.as_mcp() for tool in mcp_server.TOOLS]})
                return
            self._send(404, {"ok": False, "error": "route not found"})
        except mcp_server.McpToolError as error:
            self._send(400, {"ok": False, "error": str(error)})
        except Exception:
            self._send(500, {"ok": False, "error": "Buddy runtime failed safely"})

    def do_POST(self) -> None:
        if not self._require_access():
            return
        if self.path != "/v1/call":
            self._send(404, {"ok": False, "error": "route not found"})
            return
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError:
            self._send(400, {"ok": False, "error": "invalid content length"})
            return
        if length < 1 or length > self._runtime().buddy_settings.max_request_bytes:
            self._send(413, {"ok": False, "error": "request body size is not allowed"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, {"ok": False, "error": "request body must be valid JSON"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"ok": False, "error": "request body must be an object"})
            return
        tool = payload.get("tool")
        arguments = payload.get("arguments", {})
        if not isinstance(tool, str) or not isinstance(arguments, dict):
            self._send(400, {"ok": False, "error": "tool and object arguments are required"})
            return
        try:
            result = mcp_server.call_tool(self._runtime().buddy_config, tool, arguments)
            self._send(200, {"ok": True, "result": result})
        except mcp_server.McpToolError as error:
            self._send(400, {"ok": False, "error": str(error)})
        except Exception:
            self._send(500, {"ok": False, "error": "Buddy runtime failed safely"})


def create_server(
    settings: BridgeSettings,
    *,
    config: mcp_server.BuddyMcpConfig | None = None,
) -> BuddyHTTPServer:
    """Create a configured server without starting its blocking loop."""
    _register_runtime()
    if not _is_loopback_host(settings.host):
        if not settings.allow_remote:
            raise RuntimeError("non-loopback binding requires BUDDY_HTTP_ALLOW_REMOTE=1")
        if not settings.token:
            raise RuntimeError("non-loopback binding requires BUDDY_HTTP_TOKEN")
    selected = config or mcp_server.BuddyMcpConfig.from_env()
    return BuddyHTTPServer((settings.host, settings.port), config=selected, settings=settings)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve the local Buddy game/runtime bridge")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--self-test", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = BridgeSettings.from_env(host=args.host, port=args.port)
    if args.self_test:
        _register_runtime()
        payload = {
            "ok": True,
            "host": settings.host,
            "port": settings.port,
            "loopback": _is_loopback_host(settings.host),
            "token_required": settings.token is not None,
            "tool_count": len(mcp_server.TOOLS),
        }
        print(json.dumps(payload, sort_keys=True))
        return 0
    server = create_server(settings)
    print(f"Buddy runtime bridge listening on http://{settings.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
