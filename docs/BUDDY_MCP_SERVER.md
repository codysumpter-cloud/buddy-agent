# Buddy MCP Server

Buddy Agent should expose a local **stdio MCP server** so Odysseus, Codex, and other MCP clients can call Buddy tools without forking Odysseus.

## Current v1 shape

The standalone plugin package built for this integration exposes these tools:

| Tool | Purpose | Default risk |
| --- | --- | --- |
| `buddy.self_test` | Confirm the server is reachable. | Read-only |
| `buddy.status` | Show runtime status and paths. | Read-only |
| `buddy.project_context` | Read known project metadata files. | Read-only |
| `buddy.vault_search` | Search local Markdown vault notes. | Read-only |
| `buddy.repo_overview` | Inspect repo markers/branch without shell commands. | Read-only |
| `buddy.codex_delegate` | Write a Codex task brief under `.buddy/codex-delegations/`. | Scoped write |

## Why standalone first

Odysseus is already an MCP client surface, and Codex can consume MCP servers. Buddy does not need to modify Odysseus to become useful there. The safer path is:

```text
Odysseus / Codex / ChatGPT-assisted workflow
        ↓
Buddy MCP server
        ↓
BUAP, knowledge-vault, local repos, Codex delegation briefs
```

## Codex config

```toml
[mcp_servers.buddy]
command = "/absolute/path/to/buddy-mcp-plugin/.venv/bin/buddy-mcp"
args = []
env = { BUDDY_VAULT_PATH = "/Users/prismtek/Prismtek/knowledge-vault" }
```

## Odysseus config

Add a local/stdio MCP integration:

```text
Name: buddy
Command: /absolute/path/to/buddy-mcp-plugin/.venv/bin/buddy-mcp
Args: none
```

Smoke tool:

```text
buddy.self_test
```

If Odysseus shows the server connected but chat/agents cannot call the tools, refresh/re-index the MCP tool catalog or restart Odysseus.

## Safety defaults

- No arbitrary shell execution in v1.
- No automatic Codex launch in v1.
- Codex handoff is a local delegation brief.
- Vault search stays inside the configured vault path.
- The server is intended for private/local MCP clients.
