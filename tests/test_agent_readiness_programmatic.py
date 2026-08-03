import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest

from buddy_agent.agent_readiness.programmatic import (
    OpenAIProgrammaticAdapter,
    ProgrammaticApprovalRequired,
    ProgrammaticExecutionContext,
    ProgrammaticExecutionError,
    ProgrammaticPolicyError,
    ProgrammaticRunError,
    ProgrammaticToolDefinition,
    ProgrammaticToolPolicy,
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "integer"}},
    "required": ["value"],
    "additionalProperties": False,
}
TOOL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "integer"}},
    "required": ["value"],
    "additionalProperties": False,
}
FINAL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
    "additionalProperties": False,
}


async def echo(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"value": arguments["value"]}


def tool(
    *,
    handler=echo,
    requires_approval: bool = False,
    network_hosts: tuple[str, ...] = (),
) -> ProgrammaticToolDefinition:
    return ProgrammaticToolDefinition(
        name="echo",
        description="Return the supplied integer.",
        input_schema=INPUT_SCHEMA,
        output_schema=TOOL_OUTPUT_SCHEMA,
        handler=handler,
        requires_approval=requires_approval,
        network_hosts=network_hosts,
    )


def policy(
    *,
    max_calls: int = 2,
    max_runtime_ms: int = 2_000,
    approval: str = "policy",
    network: str = "none",
    network_allowlist: tuple[str, ...] = (),
) -> ProgrammaticToolPolicy:
    return ProgrammaticToolPolicy(
        eligible_tools=("echo",),
        max_calls=max_calls,
        max_runtime_ms=max_runtime_ms,
        network=network,  # type: ignore[arg-type]
        network_allowlist=network_allowlist,
        output_schema=FINAL_OUTPUT_SCHEMA,
        approval=approval,  # type: ignore[arg-type]
    )


class FakeFunctionTool:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeProgrammaticToolCallingTool:
    name = "programmatic_tool_calling"


class FakeModelSettings:
    def __init__(self, **kwargs: Any) -> None:
        self.values = kwargs


class FakeAgent:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeRunner:
    behavior = "success"
    seen_agent: FakeAgent | None = None

    @classmethod
    async def run(cls, agent: FakeAgent, objective: str, *, max_turns: int) -> Any:
        cls.seen_agent = agent
        assert objective
        assert max_turns >= 3
        if cls.behavior == "sleep":
            await asyncio.sleep(10)
        selected = agent.tools[1]
        await selected.on_invoke_tool(
            SimpleNamespace(tool_call_id="call-1"),
            json.dumps({"value": 7}),
        )
        return SimpleNamespace(final_output=json.dumps({"ok": True}))


FAKE_SDK = SimpleNamespace(
    Agent=FakeAgent,
    FunctionTool=FakeFunctionTool,
    ModelSettings=FakeModelSettings,
    ProgrammaticToolCallingTool=FakeProgrammaticToolCallingTool,
    Runner=FakeRunner,
)


def test_adapter_is_disabled_by_default():
    adapter = OpenAIProgrammaticAdapter(policy(), (tool(),), sdk_module=FAKE_SDK)
    with pytest.raises(PermissionError, match="disabled"):
        asyncio.run(adapter.run("Use echo"))


def test_sdk_surface_has_one_programmatic_coordinator_and_programmatic_only_tools():
    FakeRunner.behavior = "success"
    adapter = OpenAIProgrammaticAdapter(
        policy(),
        (tool(),),
        enabled=True,
        sdk_module=FAKE_SDK,
    )
    result = asyncio.run(adapter.run("Use echo"))
    assert result.output == {"ok": True}
    assert FakeRunner.seen_agent is not None
    coordinator = FakeRunner.seen_agent.tools[0]
    wrapped = FakeRunner.seen_agent.tools[1]
    assert coordinator.name == "programmatic_tool_calling"
    assert wrapped.allowed_callers == ["programmatic"]
    assert wrapped.needs_approval is False
    assert FakeRunner.seen_agent.model_settings.values["tool_choice"] == "programmatic_tool_calling"
    assert FakeRunner.seen_agent.model_settings.values["extra_args"] == {"max_tool_calls": 2}


def test_success_receipt_is_complete_and_excludes_raw_payloads():
    FakeRunner.behavior = "success"
    adapter = OpenAIProgrammaticAdapter(
        policy(),
        (tool(),),
        enabled=True,
        sdk_module=FAKE_SDK,
    )
    result = asyncio.run(adapter.run("Use echo with a bounded input"))
    receipt = result.receipt.to_dict()
    assert receipt["status"] == "completed"
    assert receipt["trace_complete"] is True
    assert receipt["raw_prompt"] == "excluded"
    assert receipt["raw_generated_code"] == "excluded"
    assert receipt["raw_tool_arguments"] == "excluded"
    assert receipt["raw_tool_outputs"] == "excluded"
    calls = receipt["tool_calls"]
    assert isinstance(calls, list)
    assert calls[0]["status"] == "completed"
    serialized = json.dumps(receipt)
    assert "Use echo with a bounded input" not in serialized
    assert '"value": 7' not in serialized


def test_unregistered_eligible_tool_is_rejected():
    with pytest.raises(ProgrammaticPolicyError, match="not registered"):
        ProgrammaticExecutionContext(policy(), ())


def test_network_contract_rejects_tools_outside_policy():
    with pytest.raises(ProgrammaticPolicyError, match="network access"):
        ProgrammaticExecutionContext(policy(), (tool(network_hosts=("example.com",)),))
    with pytest.raises(ProgrammaticPolicyError, match="non-allowlisted"):
        ProgrammaticExecutionContext(
            policy(
                network="allowlist",
                network_allowlist=("api.example.com",),
            ),
            (tool(network_hosts=("other.example.com",)),),
        )


def test_secret_like_arguments_are_rejected_without_raw_receipt_data():
    context = ProgrammaticExecutionContext(policy(), (tool(),))
    with pytest.raises(ProgrammaticExecutionError, match="secret-like"):
        asyncio.run(
            context.invoke(
                "echo",
                {"value": 1, "api_token": "sensitive"},
                "call-secret",
            )
        )
    assert context.receipts[0].status == "failed"
    assert context.receipts[0].output_sha256 is None
    assert "sensitive" not in json.dumps(context.receipts[0].to_dict())


def test_call_count_limit_is_enforced():
    context = ProgrammaticExecutionContext(policy(max_calls=1), (tool(),))
    assert asyncio.run(context.invoke("echo", {"value": 1}, "call-1")) == {"value": 1}
    with pytest.raises(ProgrammaticExecutionError, match="call limit"):
        asyncio.run(context.invoke("echo", {"value": 2}, "call-2"))
    assert len(context.receipts) == 1


def test_nested_tool_approval_is_required_and_attributed():
    context = ProgrammaticExecutionContext(policy(), (tool(requires_approval=True),))
    with pytest.raises(ProgrammaticApprovalRequired):
        asyncio.run(context.invoke("echo", {"value": 1}, "call-no-handler"))

    requests = []

    async def reject(request):
        requests.append(request)
        return False

    rejected = ProgrammaticExecutionContext(
        policy(),
        (tool(requires_approval=True),),
        approval_handler=reject,
    )
    with pytest.raises(ProgrammaticExecutionError, match="approval rejected"):
        asyncio.run(rejected.invoke("echo", {"value": 2}, "call-rejected"))
    assert requests[0].call_id == "call-rejected"
    assert requests[0].tool_name == "echo"
    assert requests[0].input_sha256
    assert rejected.receipts[0].status == "rejected"
    assert rejected.receipts[0].approval_granted is False


def test_tool_output_schema_is_enforced():
    async def invalid(_arguments):
        return {"wrong": 1}

    context = ProgrammaticExecutionContext(policy(), (tool(handler=invalid),))
    with pytest.raises(ProgrammaticExecutionError, match="missing required property value"):
        asyncio.run(context.invoke("echo", {"value": 1}, "call-invalid-output"))
    assert context.receipts[0].status == "failed"
    assert context.receipts[0].error_class == "ProgrammaticExecutionError"


def test_operator_cancellation_stops_the_sdk_run_and_returns_evidence():
    FakeRunner.behavior = "sleep"
    adapter = OpenAIProgrammaticAdapter(
        policy(max_runtime_ms=5_000),
        (tool(),),
        enabled=True,
        sdk_module=FAKE_SDK,
    )

    async def scenario() -> ProgrammaticRunError:
        cancellation = asyncio.Event()
        task = asyncio.create_task(adapter.run("Long run", cancel_event=cancellation))
        await asyncio.sleep(0.01)
        cancellation.set()
        with pytest.raises(ProgrammaticRunError) as captured:
            await task
        return captured.value

    error = asyncio.run(scenario())
    assert error.receipt.status == "cancelled"
    assert error.receipt.raw_generated_code == "excluded"


def test_wall_clock_limit_stops_the_sdk_run():
    FakeRunner.behavior = "sleep"
    adapter = OpenAIProgrammaticAdapter(
        policy(max_runtime_ms=100),
        (tool(),),
        enabled=True,
        sdk_module=FAKE_SDK,
    )
    with pytest.raises(ProgrammaticRunError) as captured:
        asyncio.run(adapter.run("Timed run"))
    assert captured.value.receipt.status == "timed_out"
