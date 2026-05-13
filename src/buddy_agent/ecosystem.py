"""Registry of planned Buddy Agent ecosystem integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskTier = Literal["standard", "review", "restricted"]


@dataclass(frozen=True)
class EcosystemIntegration:
    """A planned native integration target."""

    name: str
    repository: str
    group: str
    landing_zone: str
    risk_tier: RiskTier = "standard"
    enabled_by_default: bool = False


ECOSYSTEM_INTEGRATIONS: tuple[EcosystemIntegration, ...] = (
    EcosystemIntegration(
        "Hermes Ecosystem",
        "codysumpter-cloud/hermes-ecosystem",
        "runtime",
        "buddy_agent.runtime",
    ),
    EcosystemIntegration(
        "Hermes Workspace",
        "codysumpter-cloud/hermes-workspace",
        "runtime",
        "buddy_agent.runtime",
    ),
    EcosystemIntegration("Hermes Wiki", "codysumpter-cloud/Hermes-Wiki", "runtime", "docs"),
    EcosystemIntegration(
        "Awesome Hermes Agent",
        "codysumpter-cloud/awesome-hermes-agent",
        "discovery",
        "docs",
    ),
    EcosystemIntegration(
        "Hermes Control Interface",
        "codysumpter-cloud/hermes-control-interface",
        "ui",
        "buddy_agent.ui",
    ),
    EcosystemIntegration(
        "Hermes Web UI",
        "codysumpter-cloud/hermes-webui",
        "ui",
        "buddy_agent.ui",
    ),
    EcosystemIntegration(
        "Hermes HUD UI",
        "codysumpter-cloud/hermes-hudui",
        "ui",
        "buddy_agent.ui",
    ),
    EcosystemIntegration(
        "Prismtek Apps",
        "codysumpter-cloud/prismtek-apps",
        "product",
        "buddy_agent.app_bridge",
    ),
    EcosystemIntegration(
        "Agent Memory",
        "codysumpter-cloud/agentmemory",
        "memory",
        "buddy_agent.memory",
    ),
    EcosystemIntegration(
        "Caveman",
        "codysumpter-cloud/caveman",
        "skills",
        "buddy_agent.skills",
    ),
    EcosystemIntegration(
        "Arcade MCP",
        "codysumpter-cloud/arcade-mcp",
        "mcp",
        "buddy_agent.mcp",
    ),
    EcosystemIntegration(
        "PixelLab MCP",
        "codysumpter-cloud/pixellab-mcp",
        "mcp",
        "buddy_agent.mcp",
    ),
    EcosystemIntegration(
        "PixelLab JS",
        "codysumpter-cloud/pixellab-js",
        "creative",
        "buddy_agent.creative",
    ),
    EcosystemIntegration(
        "LibreSprite",
        "codysumpter-cloud/LibreSprite",
        "creative",
        "buddy_agent.creative",
    ),
    EcosystemIntegration(
        "Tamagoscii",
        "codysumpter-cloud/tamagoscii",
        "creative",
        "buddy_agent.creative",
    ),
    EcosystemIntegration(
        "OpenMythos",
        "codysumpter-cloud/OpenMythos",
        "mythos",
        "buddy_agent.mythos",
    ),
    EcosystemIntegration(
        "Symphony",
        "codysumpter-cloud/symphony",
        "mythos",
        "buddy_agent.mythos",
    ),
    EcosystemIntegration("Gemma", "codysumpter-cloud/gemma", "models", "buddy_agent.models"),
    EcosystemIntegration(
        "MoneyPrinterV2",
        "codysumpter-cloud/MoneyPrinterV2",
        "experiments",
        "buddy_agent.experiments",
        risk_tier="restricted",
    ),
    EcosystemIntegration(
        "bettingAI",
        "erikbohne/bettingAI",
        "experiments",
        "buddy_agent.experiments",
        risk_tier="restricted",
    ),
)


def integrations_by_group(group: str) -> tuple[EcosystemIntegration, ...]:
    """Return integrations in a group."""
    return tuple(
        integration
        for integration in ECOSYSTEM_INTEGRATIONS
        if integration.group == group
    )


def restricted_integrations() -> tuple[EcosystemIntegration, ...]:
    """Return integrations that require explicit review before enablement."""
    return tuple(
        integration
        for integration in ECOSYSTEM_INTEGRATIONS
        if integration.risk_tier == "restricted"
    )
