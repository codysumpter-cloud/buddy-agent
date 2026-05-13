from buddy_agent.ecosystem import (
    ECOSYSTEM_INTEGRATIONS,
    integrations_by_group,
    restricted_integrations,
)


def test_ecosystem_registry_includes_requested_repositories():
    repositories = {integration.repository for integration in ECOSYSTEM_INTEGRATIONS}

    assert "codysumpter-cloud/hermes-ecosystem" in repositories
    assert "codysumpter-cloud/awesome-hermes-agent" in repositories
    assert "codysumpter-cloud/agentmemory" in repositories
    assert "codysumpter-cloud/hermes-control-interface" in repositories
    assert "codysumpter-cloud/caveman" in repositories
    assert "codysumpter-cloud/arcade-mcp" in repositories
    assert "codysumpter-cloud/pixellab-js" in repositories
    assert "erikbohne/bettingAI" in repositories


def test_ecosystem_registry_groups_ui_integrations():
    names = {integration.name for integration in integrations_by_group("ui")}

    assert names == {"Hermes Control Interface", "Hermes Web UI", "Hermes HUD UI"}


def test_ecosystem_registry_groups_discovery_and_skills():
    discovery = {integration.name for integration in integrations_by_group("discovery")}
    skills = {integration.name for integration in integrations_by_group("skills")}

    assert discovery == {"Awesome Hermes Agent"}
    assert "Caveman" in skills


def test_restricted_integrations_are_disabled_by_default():
    restricted = restricted_integrations()

    assert {integration.name for integration in restricted} == {"MoneyPrinterV2", "bettingAI"}
    assert all(not integration.enabled_by_default for integration in restricted)
