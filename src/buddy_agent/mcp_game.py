"""MCP tools used by Prismtek Buddies and other Buddy-enabled games."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from . import mcp_server as base
from .game_protocol import (
    ALLOWED_GAME_COMMANDS,
    PROTOCOL_VERSION,
    GameProtocolError,
    build_game_prompt,
    normalize_context,
    normalize_message,
    normalize_model_response,
)
from .game_providers import ProviderError, provider_from_env
from .game_stack_context import assemble_game_stack_context

GameHandler = Callable[[base.BuddyMcpConfig, dict[str, Any]], dict[str, Any]]

GAME_TOOLS = (
    base.ToolDefinition(
        "buddy.game.status",
        "Report the Buddy game protocol, model provider, stack context, and executable in-game command allowlist.",
        {"type": "object", "properties": {}, "additionalProperties": False},
    ),
    base.ToolDefinition(
        "buddy.game.chat",
        "Reply as Buddy inside a Prismtek game using bounded BUAP, KnowledgeVault, and Buddy Brain context.",
        {
            "type": "object",
            "properties": {
                "message": {"type": "string", "minLength": 1, "maxLength": 4000},
                "context": {"type": "object", "additionalProperties": True},
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    ),
)

_REGISTERED = False


def _status(config: base.BuddyMcpConfig, _arguments: dict[str, Any]) -> dict[str, Any]:
    provider = provider_from_env()
    _stack_context, stack_receipt = assemble_game_stack_context(config, "")
    return {
        "ok": True,
        "protocol_version": PROTOCOL_VERSION,
        "provider": provider.status.to_dict(),
        "commands": list(ALLOWED_GAME_COMMANDS),
        "stack": stack_receipt.to_dict(),
        "capabilities": {
            "chat": provider.status.configured,
            "game_commands": True,
            "persistent_tasks": True,
            "durable_memory_events": True,
            "buap_policy_context": bool(stack_receipt.buap_policy_files),
            "knowledge_vault_context": stack_receipt.knowledge_vault_configured,
            "buddy_brain_governance_context": stack_receipt.buddy_brain_report_loaded,
            "omni_buddy_transport_contract": stack_receipt.omni_buddy_transport_contract,
            "repository_execution": False,
            "production_actions": False,
        },
    }


def _chat(config: base.BuddyMcpConfig, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        message = normalize_message(arguments.get("message"))
        context = normalize_context(arguments.get("context"))
        stack_context, stack_receipt = assemble_game_stack_context(config, message)
        system, user = build_game_prompt(message, context, stack_context)
        provider = provider_from_env()
        raw = provider.complete(system=system, user=user)
        response = normalize_model_response(raw)
    except (GameProtocolError, ProviderError) as error:
        raise base.McpToolError(str(error)) from error
    return {
        "ok": True,
        "protocol_version": PROTOCOL_VERSION,
        "reply": response["reply"],
        "commands": response["commands"],
        "provider": provider.status.to_dict(),
        "stack": stack_receipt.to_dict(),
        "claims": {
            "commands_proposed_not_executed": True,
            "game_client_must_validate": True,
            "stack_context_is_bounded": True,
            "knowledge_evidence_may_be_incomplete": True,
        },
    }


GAME_HANDLERS: dict[str, GameHandler] = {
    "buddy.game.status": _status,
    "buddy.game.chat": _chat,
}


def register_game_tools() -> None:
    """Add the stable Buddy game tool family exactly once."""
    global _REGISTERED
    if _REGISTERED:
        return
    additions = tuple(tool for tool in GAME_TOOLS if tool.name not in base.TOOL_BY_NAME)
    if additions:
        # mcp_server.TOOLS was inferred as a fixed-length tuple from its literals.
        # Runtime composition intentionally extends it, so mutate through the module
        # object rather than weakening every ToolDefinition call site to Any.
        base_module = cast(Any, base)
        base_module.TOOLS = (*base.TOOLS, *additions)
        base.TOOL_BY_NAME.update({tool.name: tool for tool in additions})
        handlers = cast(dict[str, GameHandler], base.TOOL_HANDLERS)
        handlers.update(GAME_HANDLERS)
    _REGISTERED = True
