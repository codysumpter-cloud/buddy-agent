import json

from buddy_agent.integrations import (
    BuddyIntegrationRuntime,
    build_work_run_plan,
    get_integration_target,
    get_variant_config,
    integration_summary_lines,
    load_workflow,
    validate_integration_targets,
)


def write_workflow(tmp_path, *, tracker_path=None):
    workflow = tmp_path / "WORKFLOW.md"
    tracker_line = f"  path: {tracker_path}\n" if tracker_path else ""
    workflow.write_text(
        "---\n"
        "tracker:\n"
        "  kind: local-json\n"
        f"{tracker_line}"
        "workspace:\n"
        f"  root: {tmp_path / 'workspaces'}\n"
        "hooks:\n"
        "  after_create: echo ready\n"
        "agent:\n"
        "  max_turns: 20\n"
        "codex:\n"
        "  command: codex app-server\n"
        "---\n"
        "Work on {{ issue.identifier }}: {{ issue.title }}.\n"
        "\n"
        "{{ issue.body }}\n",
        encoding="utf-8",
    )
    return workflow


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


def test_openmythos_target_has_native_runtime_capabilities():
    target = get_integration_target("openmythos")

    assert target.status == "native-runtime"
    assert target.get_capability("architecture-contract").status == "native-runtime"
    assert target.get_capability("variant-configs").status == "native-runtime"
    assert target.get_capability("training-script").status == "native-runtime"
    assert target.get_capability("torch-model").status == "adapter-ready"


def test_openmythos_architecture_contract_runs_without_torch():
    result = BuddyIntegrationRuntime().run("openmythos", "architecture-contract")

    assert result.ok is True
    assert result.status == "native-runtime"
    assert "stages=prelude,recurrent_block,coda" in result.message
    assert "torch_backend=" in result.message


def test_openmythos_named_variant_config_is_valid():
    config = get_variant_config("buddy-mythos-3b")

    assert config.name == "buddy-mythos-3b"
    assert config.validate() == ()
    assert config.parameter_estimate() > 0


def test_openmythos_variant_configs_runtime_lists_variants():
    result = BuddyIntegrationRuntime().run("openmythos", "variant-configs")

    assert result.ok is True
    assert "buddy-mythos-tiny" in result.message
    assert "buddy-mythos-7b" in result.message


def test_openmythos_torch_backend_guard_does_not_require_torch():
    result = BuddyIntegrationRuntime().run("openmythos", "torch-model")

    assert result.ok is True
    assert result.status == "adapter-ready"
    assert "torch_backend=" in result.message
    assert "backend_import_guard=ok" in result.message


def test_openmythos_training_script_returns_plan_only():
    result = BuddyIntegrationRuntime().run("openmythos", "training-script", path="buddy-mythos-1b")

    assert result.ok is True
    assert result.status == "native-runtime"
    assert "variant=buddy-mythos-1b" in result.message
    assert "default_action=plan_only_no_training_started" in result.message


def test_symphony_target_has_native_runtime_capabilities():
    target = get_integration_target("symphony")

    assert target.status == "native-runtime"
    assert target.get_capability("workflow-contract").status == "native-runtime"
    assert target.get_capability("tracker-local").status == "native-runtime"
    assert target.get_capability("workspace-spawn").status == "native-runtime"
    assert target.get_capability("work-runner").status == "native-runtime"
    assert target.get_capability("observability").status == "native-runtime"
    assert target.get_capability("codex-app-server").status == "adapter-ready"


def test_symphony_workflow_contract_schema_runs_without_external_services():
    result = BuddyIntegrationRuntime().run("symphony", "workflow-contract")

    assert result.ok is True
    assert result.status == "native-runtime"
    assert "workflow contract ready" in result.message


def test_symphony_workflow_contract_validates_file(tmp_path):
    workflow = write_workflow(tmp_path)

    result = BuddyIntegrationRuntime().run("symphony", "workflow-contract", path=workflow)

    assert result.ok is True
    assert "workflow contract valid" in result.message


def test_symphony_local_tracker_loads_json_issue(tmp_path):
    tracker = tmp_path / "issues.json"
    tracker.write_text(
        json.dumps(
            [
                {
                    "identifier": "BUDDY-42",
                    "title": "Build local work runner",
                    "body": "Make the vertical slice real.",
                    "priority": "high",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = BuddyIntegrationRuntime().run("symphony", "tracker-local", path=tracker)

    assert result.ok is True
    assert "next_issue=BUDDY-42" in result.message
    assert "priority=high" in result.message


def test_symphony_workspace_plan_renders_prompt(tmp_path):
    tracker = tmp_path / "issues.json"
    tracker.write_text(
        json.dumps({"identifier": "BUDDY-7", "title": "Plan workspace", "body": "Ship it."}),
        encoding="utf-8",
    )
    workflow = write_workflow(tmp_path, tracker_path=tracker)

    plan = build_work_run_plan(load_workflow(workflow))

    assert plan.issue.identifier == "BUDDY-7"
    assert plan.workspace_path.name.startswith("BUDDY-7-Plan-workspace")
    assert "Work on BUDDY-7: Plan workspace." in plan.prompt
    assert "Ship it." in plan.prompt


def test_symphony_work_runner_creates_local_workspace_files(tmp_path):
    tracker = tmp_path / "issues.json"
    tracker.write_text(
        json.dumps({"identifier": "BUDDY-9", "title": "Create files", "body": "Receipt please."}),
        encoding="utf-8",
    )
    workflow = write_workflow(tmp_path, tracker_path=tracker)

    result = BuddyIntegrationRuntime().run("symphony", "work-runner", path=workflow)

    assert result.ok is True
    assert "mode=local_plan_no_external_services_started" in result.message
    workspace_line = next(line for line in result.message.splitlines() if line.startswith("workspace="))
    workspace_path = workspace_line.removeprefix("workspace=")
    assert (tmp_path / "workspaces" / "BUDDY-9-Create-files" / "BUDDY_WORK_PROMPT.md").exists()
    assert (tmp_path / "workspaces" / "BUDDY-9-Create-files" / "buddy_work_run.json").exists()
    assert workspace_path.endswith("BUDDY-9-Create-files")


def test_symphony_codex_bridge_is_adapter_ready_not_launched():
    result = BuddyIntegrationRuntime().run("symphony", "codex-app-server")

    assert result.ok is True
    assert result.status == "adapter-ready"
    assert "default_action=plan_only_no_process_started" in result.message


def test_adapter_ready_hermes_capability_does_not_fake_runtime_completion():
    result = BuddyIntegrationRuntime().run("hermes-agent", "model-routing")

    assert result.ok is False
    assert result.status == "adapter-ready"
    assert "adapter-ready" in result.message
