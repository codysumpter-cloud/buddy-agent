"""Runtime adapters for Buddy control-plane and observability integrations.

This package intentionally keeps external credentials and raw traces out of
repository files. Runtime callers inject AgentRQ/MCP transports and opt into
Monocle setup through environment or explicit config.
"""

from .agentrq import AgentRQClient, AgentRQTask, ToolTransport
from .knowledge_vault import KnowledgeVaultEmitter
from .monocle import MonocleAdapter, TraceSummary
from .runtime_adapter import ControlPlaneRuntimeAdapter
from .sanitizer import SanitizationError, Sanitizer

__all__ = [
    "AgentRQClient",
    "AgentRQTask",
    "ControlPlaneRuntimeAdapter",
    "KnowledgeVaultEmitter",
    "MonocleAdapter",
    "SanitizationError",
    "Sanitizer",
    "ToolTransport",
    "TraceSummary",
]
