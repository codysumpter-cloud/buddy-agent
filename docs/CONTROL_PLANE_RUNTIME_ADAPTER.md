# Control Plane Runtime Adapter Usage

Status: initial live adapter  
Package: `buddy_agent.control_plane`

## What this adapter does

The runtime adapter connects three safe surfaces:

1. **AgentRQ-compatible task control plane** through an injected MCP/tool transport.
2. **Monocle-compatible observability** through optional lazy `monocle_apptrace` setup and sanitized trace summaries.
3. **Knowledge Vault receipts** through schema-shaped event drafts that exclude raw prompts, raw traces, secrets, browser sessions, and private paths.

It does **not** commit credentials, read `.mcp.json`, store tokenized URLs, export raw traces, or write directly to compiled Knowledge Vault graph outputs.

## Minimal usage

```python
from buddy_agent.control_plane import (
    AgentRQClient,
    ControlPlaneRuntimeAdapter,
    KnowledgeVaultEmitter,
    MonocleAdapter,
)

class RuntimeToolTransport:
    def call_tool(self, name, arguments=None):
        # Call the already-configured AgentRQ MCP/tool runtime here.
        # Do not store tokens in repo code.
        ...

client = AgentRQClient(RuntimeToolTransport(), workspace_alias="buddy-agent-runtime")
adapter = ControlPlaneRuntimeAdapter(
    agentrq=client,
    monocle=MonocleAdapter(enabled=True, workflow_name="buddy-agent-runtime"),
    knowledge_vault=KnowledgeVaultEmitter(),
)

result = adapter.run_next_task(lambda task: {
    "summary": f"Handled {task.title}",
    "tool_categories": ["runtime", "github"],
})

# The event is safe to hand to a reviewed Knowledge Vault inbox path.
print(result.event)
```

## Transport contract

The injected transport must expose:

```python
def call_tool(name: str, arguments: dict | None = None): ...
```

Allowed AgentRQ-style tool names:

- `getWorkspace`
- `getNextTask`
- `getTaskMessages`
- `reply`
- `updateTaskStatus`
- `downloadAttachment`

Attachment download remains denied unless `AgentRQClient(..., allow_attachments=True)` is set by caller policy.

## Monocle behavior

`MonocleAdapter(enabled=True)` imports `monocle_apptrace` lazily and calls `setup_monocle_telemetry(workflow_name=...)` when available. If the optional dependency is missing, it returns a sanitized unavailable status and does not break Buddy startup.

Raw traces are private runtime artifacts. Receipts include only summary fields like workflow, status, duration, tool categories, error class, and assertions.

## Knowledge Vault behavior

`KnowledgeVaultEmitter` builds events with:

- `event_id`
- `event_type`
- `source`
- `timestamp`
- `payload`

It can write an event only to a caller-supplied local inbox directory. It rejects duplicate event IDs and never mutates compiled graph outputs.

## Validation

Run:

```bash
python -m pytest tests/test_control_plane_runtime_adapter.py
```

The test suite covers:

- AgentRQ task lifecycle updates.
- sanitized Knowledge Vault event generation.
- tokenized URL and secret redaction.
- raw trace and raw prompt blocking.
- default attachment download denial.
- denial of silent approval.
