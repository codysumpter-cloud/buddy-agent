from buddy_agent.integrations import (
    BuddyIntegrationRuntime,
    get_integration_target,
    integration_summary_lines,
    validate_integration_targets,
)


def test_required_integration_targets_are_registered():
    assert validate_integration_targets() == ()
    summary = "\n".join(integration_summary_lines())

    assert "hermes-agent:" in summary
    assert "symphony:" in summary
    assert "openmythos:" in summary


def test_hermes_agent_is_not_marked_fully_native():
    target = get_integration_target("hermes-agent")

    assert target.status == "adapter-ready"
    assert target.get_capability("terminal-chat").status == "mapped"
    assert target.get_capability("memory").status == "adapter-ready"
    assert target.get_capability("skills").status == "mapped"


def test_openmythos_architecture_contract_runs_without_torch():
    runtime = BuddyIntegrationRuntime()

    result = runtime.run("openmythos", "architecture-contract")

    assert result.ok is True
    assert result.status == "native-runtime"
    assert "stages=prelude,recurrent_block,coda" in result.message
    assert "torch_backend=optional_not_default" in result.message


def test_symphony_workflow_contract_schema_runs_without_external_services():
    runtime = BuddyIntegrationRuntime()

    result = runtime.run("symphony", "workflow-contract")

    assert result.ok is True
    assert result.status == "native-runtime"
    assert "workflow contract ready" in result.message


def test_symphony_workflow_contract_validates_file(tmp_path):
    workflow = tmp_path / "WORKFLOW.md"
    workflow.write_text(
        "---\n"
        "tracker:\n"
        "  kind: linear\n"
        "workspace:\n"
        "  root: /tmp/workspaces\n"
        "hooks:\n"
        "  after_create: echo ready\n"
        "agent:\n"
        "  max_turns: 20\n"
        "codex:\n"
        "  command: codex app-server\n"
        "---\n"
        "Work on {{ issue.identifier }}.\n",
        encoding="utf-8",
    )

    result = BuddyIntegrationRuntime().run("symphony", "workflow-contract", path=workflow)

    assert result.ok is True
    assert result.message == "Symphony workflow contract valid"


def test_adapter_ready_capability_does_not_fake_runtime_completion():
    runtime = BuddyIntegrationRuntime()

    result = runtime.run("hermes-agent", "model-routing")

    assert result.ok is False
    assert result.status == "adapter-ready"
    assert "not fully native-runtime" in result.message
