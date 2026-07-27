import pytest

from buddy_agent.agent_readiness.sandbox import (
    PolicyOnlySandboxProvider,
    SandboxCapabilities,
    SandboxRequest,
    plan_request,
    profile,
)


def test_default_request_is_conservative():
    request = SandboxRequest()
    assert request.network == "none"
    assert request.filesystem == "workspace-write"
    assert request.secrets == "none"


def test_review_profile_requires_enforced_readonly_and_no_network():
    capabilities = SandboxCapabilities("local-process", False, False, False, True, False, False, True)
    plan = plan_request(capabilities, profile("review"))
    assert not plan.executable
    assert "network:none" in plan.missing_enforcement
    assert "filesystem:readonly" in plan.missing_enforcement


def test_release_provider_requires_human_approval_even_when_capable():
    capabilities = SandboxCapabilities("container", True, True, True, True, True, True, True)
    provider = PolicyOnlySandboxProvider(capabilities)
    with pytest.raises(PermissionError):
        provider.create(profile("release"))
