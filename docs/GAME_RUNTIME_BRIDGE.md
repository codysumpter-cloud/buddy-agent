# Buddy Game Runtime Bridge

`buddy-serve` exposes the packaged Buddy MCP runtime to native and Web game clients without embedding credentials in a Godot export.

## Start locally

```bash
python -m pip install -e .
BUDDY_PROVIDER=ollama BUDDY_MODEL=qwen3:8b buddy-serve
```

OpenAI Responses is also supported:

```bash
OPENAI_API_KEY=... BUDDY_PROVIDER=openai BUDDY_MODEL=gpt-5-mini buddy-serve
```

The default listener is `127.0.0.1:8765`. It provides:

- `GET /health`
- `GET /v1/tools`
- `POST /v1/call`

Example call:

```json
{
  "tool": "buddy.game.chat",
  "arguments": {
    "message": "Use the computer, then start my focus timer.",
    "context": {
      "game": "prismtek-buddies",
      "mode": "play",
      "nearby_items": [
        { "asset_id": "anim-computer-macbook-ani", "interaction": "work" }
      ]
    }
  }
}
```

The response contains player-facing text and zero or more proposed commands from the fixed game allowlist. Commands are **not executed by the server**. The game must validate current state, item identity, mode, coordinates, and user intent before executing them.

## Browser and remote safety

Loopback is the default and requires no token. Browser origins are limited to Prismtek domains and local development origins.

A non-loopback bind is refused unless both are configured:

```bash
BUDDY_HTTP_ALLOW_REMOTE=1
BUDDY_HTTP_TOKEN=<strong random token>
```

Remote clients must then send `Authorization: Bearer <token>`. The token is never returned by health or status endpoints.

## Provider capability evidence

`buddy.game.status` reports the selected provider and whether chat is configured. The local bridge supports:

- OpenAI Responses API through `OPENAI_API_KEY`;
- Ollama chat through `OLLAMA_CHAT_URL`;
- an explicit disabled mode for deterministic tests and offline status.

Provider output is treated as untrusted. Invalid commands are dropped, secret-like context keys are redacted, and plain-text model output becomes a text-only response.

## Full-stack composition

The HTTP bridge registers the same runtime used by `buddy-mcp`:

- project and KnowledgeVault context tools;
- persistent task lifecycle and human approvals;
- public-safe Vegapunk lifecycle events;
- game status/chat tools.

Repository execution remains outside the game HTTP tool family. `buddy-exec` still requires a separately approved, running task and emits its own evidence. The bridge does not claim container, network, release, merge, or production-deployment authority.
