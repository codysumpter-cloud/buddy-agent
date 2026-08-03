"""Bounded experimental OpenAI Programmatic Tool Calling adapter.

The hosted JavaScript coordinator is treated as a distinct invocation mode. Buddy
owns tool eligibility, approvals, budgets, cancellation, schema validation, and
sanitized receipts around the optional OpenAI Agents SDK integration.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
import re
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, cast

InvocationMode = Literal[
    "direct_tool_call",
    "programmatic_tool_call",
    "subagent",
    "human_action",
]
ProgrammaticNetworkMode = Literal["none", "allowlist"]
ProgrammaticSecretMode = Literal["none", "scoped"]
ProgrammaticApprovalMode = Literal["required", "policy"]
GeneratedCodeRetention = Literal["discard", "hash_only"]
ToolHandler = Callable[[Mapping[str, Any]], Awaitable[Any]]

_TOOL_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_SECRET_KEY = re.compile(
    r"(?:^|_)(?:api_key|token|secret|password|private_key|credential)(?:$|_)",
    re.IGNORECASE,
)


class ProgrammaticPolicyError(ValueError):
    """The requested programmatic policy cannot be enforced safely."""


class ProgrammaticExecutionError(RuntimeError):
    """A bounded programmatic tool call failed."""


class ProgrammaticApprovalRequired(ProgrammaticExecutionError):
    """A tool call needs an approval handler before it may execute."""


class ProgrammaticCancelled(ProgrammaticExecutionError):
    """The operator cancelled a programmatic run."""


class ProgrammaticRunError(ProgrammaticExecutionError):
    """A run failed and carries its sanitized receipt."""

    def __init__(self, message: str, receipt: ProgrammaticRunReceipt) -> None:
        super().__init__(message)
        self.receipt = receipt


@dataclass(frozen=True)
class ProgrammaticToolPolicy:
    eligible_tools: tuple[str, ...]
    max_calls: int = 8
    max_runtime_ms: int = 60_000
    network: ProgrammaticNetworkMode = "none"
    network_allowlist: tuple[str, ...] = ()
    output_schema: Mapping[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "additionalProperties": True,
        }
    )
    secrets: ProgrammaticSecretMode = "none"
    approval: ProgrammaticApprovalMode = "required"
    generated_code_retention: GeneratedCodeRetention = "discard"

    def __post_init__(self) -> None:
        if not self.eligible_tools:
            raise ProgrammaticPolicyError("eligible_tools must not be empty")
        if len(set(self.eligible_tools)) != len(self.eligible_tools):
            raise ProgrammaticPolicyError("eligible_tools must be unique")
        for name in self.eligible_tools:
            if not _TOOL_NAME.fullmatch(name):
                raise ProgrammaticPolicyError(f"invalid eligible tool name: {name!r}")
        if self.max_calls < 1 or self.max_calls > 100:
            raise ProgrammaticPolicyError("max_calls must be between 1 and 100")
        if self.max_runtime_ms < 100 or self.max_runtime_ms > 3_600_000:
            raise ProgrammaticPolicyError("max_runtime_ms must be between 100 and 3600000")
        if self.network == "allowlist" and not self.network_allowlist:
            raise ProgrammaticPolicyError("network_allowlist is required when network=allowlist")
        if self.network != "allowlist" and self.network_allowlist:
            raise ProgrammaticPolicyError("network_allowlist is only valid when network=allowlist")
        if not isinstance(self.output_schema, Mapping):
            raise ProgrammaticPolicyError("output_schema must be a JSON Schema object")


@dataclass(frozen=True)
class ProgrammaticToolDefinition:
    name: str
    description: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any]
    handler: ToolHandler
    requires_approval: bool = False
    network_hosts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _TOOL_NAME.fullmatch(self.name):
            raise ProgrammaticPolicyError(f"invalid tool name: {self.name!r}")
        if not self.description.strip():
            raise ProgrammaticPolicyError(f"tool description is required: {self.name}")
        if not isinstance(self.input_schema, Mapping) or not isinstance(
            self.output_schema, Mapping
        ):
            raise ProgrammaticPolicyError("tool schemas must be JSON Schema objects")


@dataclass(frozen=True)
class ProgrammaticApprovalRequest:
    trace_id: str
    call_id: str
    tool_name: str
    input_sha256: str


ApprovalHandler = Callable[[ProgrammaticApprovalRequest], Awaitable[bool]]


@dataclass(frozen=True)
class ProgrammaticToolCallReceipt:
    call_id: str
    tool_name: str
    status: Literal["completed", "rejected", "failed", "cancelled", "timed_out"]
    started_at_unix_ms: int
    finished_at_unix_ms: int
    elapsed_ms: int
    input_sha256: str
    output_sha256: str | None
    approval_required: bool
    approval_granted: bool | None
    error_class: str | None = None

    def to_dict(self) -> dict[str, object]:
        return cast(dict[str, object], asdict(self))


@dataclass(frozen=True)
class ProgrammaticRunReceipt:
    schema: str
    provider: str
    model: str
    invocation_mode: InvocationMode
    trace_id: str
    status: Literal["completed", "failed", "cancelled", "timed_out"]
    started_at_unix_ms: int
    finished_at_unix_ms: int
    elapsed_ms: int
    tool_calls: tuple[ProgrammaticToolCallReceipt, ...]
    final_output_sha256: str | None
    generated_code_retention: GeneratedCodeRetention
    raw_prompt: Literal["excluded"] = "excluded"
    raw_generated_code: Literal["excluded"] = "excluded"
    raw_tool_arguments: Literal["excluded"] = "excluded"
    raw_tool_outputs: Literal["excluded"] = "excluded"

    @property
    def trace_complete(self) -> bool:
        return all(call.call_id and call.tool_name for call in self.tool_calls)

    def to_dict(self) -> dict[str, object]:
        value = cast(dict[str, object], asdict(self))
        value["tool_calls"] = [call.to_dict() for call in self.tool_calls]
        value["trace_complete"] = self.trace_complete
        return value


@dataclass(frozen=True)
class ProgrammaticRunResult:
    output: Any
    receipt: ProgrammaticRunReceipt


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _SECRET_KEY.search(str(key)) or _contains_secret_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_secret_key(item) for item in value)
    return False


def _matches_json_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
    if expected == "object":
        return isinstance(value, Mapping)
    return True


def validate_json_schema(value: Any, schema: Mapping[str, Any], path: str = "$") -> None:
    """Validate the strict subset Buddy needs for tool and final-output contracts."""
    if "enum" in schema:
        enum = schema["enum"]
        if not isinstance(enum, Sequence) or isinstance(enum, (str, bytes, bytearray)):
            raise ProgrammaticPolicyError(f"invalid enum schema at {path}")
        if value not in enum:
            raise ProgrammaticExecutionError(f"schema validation failed at {path}: not in enum")

    expected_types: tuple[str, ...]
    raw_type = schema.get("type")
    if isinstance(raw_type, str):
        expected_types = (raw_type,)
    elif isinstance(raw_type, Sequence) and not isinstance(raw_type, (str, bytes, bytearray)):
        expected_types = tuple(str(item) for item in raw_type)
    else:
        expected_types = ()
    if expected_types and not any(_matches_json_type(value, expected) for expected in expected_types):
        joined = " or ".join(expected_types)
        raise ProgrammaticExecutionError(
            f"schema validation failed at {path}: expected {joined}"
        )

    if isinstance(value, Mapping):
        properties_raw = schema.get("properties", {})
        properties = (
            cast(Mapping[str, Any], properties_raw)
            if isinstance(properties_raw, Mapping)
            else {}
        )
        required_raw = schema.get("required", ())
        required = (
            tuple(str(item) for item in required_raw)
            if isinstance(required_raw, Sequence)
            and not isinstance(required_raw, (str, bytes, bytearray))
            else ()
        )
        for key in required:
            if key not in value:
                raise ProgrammaticExecutionError(
                    f"schema validation failed at {path}: missing required property {key}"
                )
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            key_text = str(key)
            child_schema = properties.get(key_text)
            if isinstance(child_schema, Mapping):
                validate_json_schema(child, cast(Mapping[str, Any], child_schema), f"{path}.{key_text}")
            elif additional is False:
                raise ProgrammaticExecutionError(
                    f"schema validation failed at {path}: unexpected property {key_text}"
                )
            elif isinstance(additional, Mapping):
                validate_json_schema(
                    child,
                    cast(Mapping[str, Any], additional),
                    f"{path}.{key_text}",
                )

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                validate_json_schema(
                    item,
                    cast(Mapping[str, Any], item_schema),
                    f"{path}[{index}]",
                )


async def _await_with_cancel(
    awaitable: Awaitable[Any],
    *,
    timeout_seconds: float,
    cancel_event: asyncio.Event | None,
) -> Any:
    operation = asyncio.ensure_future(awaitable)
    cancellation: asyncio.Task[bool] | None = None
    try:
        if cancel_event is None:
            return await asyncio.wait_for(operation, timeout=timeout_seconds)
        cancellation = asyncio.create_task(cancel_event.wait())
        done, _ = await asyncio.wait(
            {operation, cancellation},
            timeout=timeout_seconds,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if cancellation in done and cancel_event.is_set():
            operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)
            raise ProgrammaticCancelled("programmatic run cancelled by operator")
        if operation not in done:
            operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)
            raise TimeoutError("programmatic runtime limit exceeded")
        return await operation
    finally:
        if cancellation is not None:
            cancellation.cancel()
            await asyncio.gather(cancellation, return_exceptions=True)


class ProgrammaticExecutionContext:
    """Per-run gate around every programmatic tool invocation."""

    def __init__(
        self,
        policy: ProgrammaticToolPolicy,
        tools: Sequence[ProgrammaticToolDefinition],
        *,
        approval_handler: ApprovalHandler | None = None,
        cancel_event: asyncio.Event | None = None,
        trace_id: str | None = None,
    ) -> None:
        self.policy = policy
        self.approval_handler = approval_handler
        self.cancel_event = cancel_event
        self.trace_id = trace_id or f"ptc-{uuid.uuid4().hex}"
        self.started_monotonic = time.monotonic()
        self._lock = asyncio.Lock()
        self._call_count = 0
        self._receipts: list[ProgrammaticToolCallReceipt] = []
        self.tools = {tool.name: tool for tool in tools}
        missing = sorted(set(policy.eligible_tools) - set(self.tools))
        if missing:
            raise ProgrammaticPolicyError(
                "eligible tools are not registered: " + ", ".join(missing)
            )
        extra = sorted(set(self.tools) - set(policy.eligible_tools))
        if extra:
            raise ProgrammaticPolicyError(
                "registered tools are not eligible: " + ", ".join(extra)
            )
        for tool in tools:
            if policy.network == "none" and tool.network_hosts:
                raise ProgrammaticPolicyError(
                    f"tool {tool.name} declares network access under network=none"
                )
            if policy.network == "allowlist":
                disallowed = sorted(set(tool.network_hosts) - set(policy.network_allowlist))
                if disallowed:
                    raise ProgrammaticPolicyError(
                        f"tool {tool.name} uses non-allowlisted hosts: {', '.join(disallowed)}"
                    )

    @property
    def receipts(self) -> tuple[ProgrammaticToolCallReceipt, ...]:
        return tuple(self._receipts)

    def _remaining_seconds(self) -> float:
        elapsed_ms = (time.monotonic() - self.started_monotonic) * 1000
        return max(0.0, (self.policy.max_runtime_ms - elapsed_ms) / 1000)

    async def _reserve_call(self) -> None:
        async with self._lock:
            if self.cancel_event is not None and self.cancel_event.is_set():
                raise ProgrammaticCancelled("programmatic run cancelled by operator")
            if self._remaining_seconds() <= 0:
                raise TimeoutError("programmatic runtime limit exceeded")
            if self._call_count >= self.policy.max_calls:
                raise ProgrammaticExecutionError("programmatic tool call limit exceeded")
            self._call_count += 1

    async def invoke(self, tool_name: str, arguments: Mapping[str, Any], call_id: str) -> Any:
        await self._reserve_call()
        started_epoch = int(time.time() * 1000)
        started = time.monotonic()
        input_hash = _sha256(arguments)
        approval_required = self.policy.approval == "required"
        approval_granted: bool | None = None
        output_hash: str | None = None
        status: Literal["completed", "rejected", "failed", "cancelled", "timed_out"] = "failed"
        error_class: str | None = None
        tool = self.tools.get(tool_name)
        try:
            if tool is None or tool_name not in self.policy.eligible_tools:
                raise ProgrammaticExecutionError(f"tool is unavailable: {tool_name}")
            approval_required = approval_required or tool.requires_approval
            if self.policy.secrets == "none" and _contains_secret_key(arguments):
                raise ProgrammaticExecutionError("secret-like tool arguments are not allowed")
            validate_json_schema(arguments, tool.input_schema)
            if approval_required:
                if self.approval_handler is None:
                    raise ProgrammaticApprovalRequired(
                        f"tool requires approval but no approval handler is configured: {tool_name}"
                    )
                approval_granted = await self.approval_handler(
                    ProgrammaticApprovalRequest(
                        trace_id=self.trace_id,
                        call_id=call_id,
                        tool_name=tool_name,
                        input_sha256=input_hash,
                    )
                )
                if not approval_granted:
                    status = "rejected"
                    raise ProgrammaticExecutionError(f"tool approval rejected: {tool_name}")
            remaining = self._remaining_seconds()
            if remaining <= 0:
                raise TimeoutError("programmatic runtime limit exceeded")
            output = await _await_with_cancel(
                tool.handler(arguments),
                timeout_seconds=remaining,
                cancel_event=self.cancel_event,
            )
            validate_json_schema(output, tool.output_schema)
            output_hash = _sha256(output)
            status = "completed"
            return output
        except ProgrammaticCancelled:
            status = "cancelled"
            error_class = "ProgrammaticCancelled"
            raise
        except TimeoutError:
            status = "timed_out"
            error_class = "TimeoutError"
            raise
        except Exception as error:
            error_class = error.__class__.__name__
            raise
        finally:
            finished = int(time.time() * 1000)
            self._receipts.append(
                ProgrammaticToolCallReceipt(
                    call_id=call_id,
                    tool_name=tool_name,
                    status=status,
                    started_at_unix_ms=started_epoch,
                    finished_at_unix_ms=finished,
                    elapsed_ms=int((time.monotonic() - started) * 1000),
                    input_sha256=input_hash,
                    output_sha256=output_hash,
                    approval_required=approval_required,
                    approval_granted=approval_granted,
                    error_class=error_class,
                )
            )


class OpenAIProgrammaticAdapter:
    """Experimental Agents SDK adapter, disabled unless explicitly enabled."""

    def __init__(
        self,
        policy: ProgrammaticToolPolicy,
        tools: Sequence[ProgrammaticToolDefinition],
        *,
        model: str = "gpt-5.6-luna",
        enabled: bool = False,
        approval_handler: ApprovalHandler | None = None,
        sdk_module: Any | None = None,
    ) -> None:
        self.policy = policy
        self.tools = tuple(tools)
        self.model = model.strip()
        self.enabled = enabled
        self.approval_handler = approval_handler
        self._sdk_module = sdk_module
        if not self.model:
            raise ProgrammaticPolicyError("model is required")
        ProgrammaticExecutionContext(policy, self.tools, approval_handler=approval_handler)

    def _sdk(self) -> Any:
        if self._sdk_module is not None:
            return self._sdk_module
        try:
            return importlib.import_module("agents")
        except ImportError as error:
            raise RuntimeError(
                "OpenAI Agents SDK is not installed; install buddy-agent[programmatic]"
            ) from error

    def _build_sdk_tools(self, sdk: Any, context: ProgrammaticExecutionContext) -> list[Any]:
        sdk_tools: list[Any] = [sdk.ProgrammaticToolCallingTool()]
        for definition in self.tools:

            async def invoke_tool(
                tool_context: Any,
                arguments_json: str,
                *,
                selected: ProgrammaticToolDefinition = definition,
            ) -> Any:
                raw = json.loads(arguments_json)
                if not isinstance(raw, Mapping):
                    raise ProgrammaticExecutionError("tool arguments must be a JSON object")
                call_id = str(getattr(tool_context, "tool_call_id", "") or uuid.uuid4().hex)
                return await context.invoke(
                    selected.name,
                    cast(Mapping[str, Any], raw),
                    call_id,
                )

            sdk_tools.append(
                sdk.FunctionTool(
                    name=definition.name,
                    description=definition.description,
                    params_json_schema=dict(definition.input_schema),
                    on_invoke_tool=invoke_tool,
                    strict_json_schema=True,
                    needs_approval=False,
                    timeout_seconds=max(0.1, self.policy.max_runtime_ms / 1000),
                    timeout_behavior="raise_exception",
                    allowed_callers=["programmatic"],
                    output_json_schema=dict(definition.output_schema),
                )
            )
        return sdk_tools

    async def run(
        self,
        objective: str,
        *,
        cancel_event: asyncio.Event | None = None,
    ) -> ProgrammaticRunResult:
        if not self.enabled:
            raise PermissionError("programmatic tool calling is disabled by default")
        clean_objective = objective.strip()
        if not clean_objective:
            raise ProgrammaticPolicyError("objective cannot be empty")
        started_epoch = int(time.time() * 1000)
        started = time.monotonic()
        context = ProgrammaticExecutionContext(
            self.policy,
            self.tools,
            approval_handler=self.approval_handler,
            cancel_event=cancel_event,
        )
        sdk = self._sdk()
        sdk_tools = self._build_sdk_tools(sdk, context)
        settings = sdk.ModelSettings(
            tool_choice="programmatic_tool_calling",
            parallel_tool_calls=False,
            store=False,
            extra_args={"max_tool_calls": self.policy.max_calls},
        )
        agent = sdk.Agent(
            name="Buddy Programmatic Tool Experiment",
            instructions=(
                "Use only the eligible programmatic tools. Return one JSON value matching the "
                "required final output schema. Do not request secrets or invent tool results."
            ),
            model=self.model,
            model_settings=settings,
            tools=sdk_tools,
        )
        output: Any = None
        final_hash: str | None = None
        status: Literal["completed", "failed", "cancelled", "timed_out"] = "failed"
        try:
            result = await _await_with_cancel(
                sdk.Runner.run(
                    agent,
                    clean_objective,
                    max_turns=self.policy.max_calls + 2,
                ),
                timeout_seconds=self.policy.max_runtime_ms / 1000,
                cancel_event=cancel_event,
            )
            output = getattr(result, "final_output", None)
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except json.JSONDecodeError:
                    pass
            validate_json_schema(output, self.policy.output_schema)
            final_hash = _sha256(output)
            status = "completed"
        except ProgrammaticCancelled as error:
            status = "cancelled"
            receipt = self._receipt(context, status, started_epoch, started, final_hash)
            raise ProgrammaticRunError(str(error), receipt) from error
        except TimeoutError as error:
            status = "timed_out"
            receipt = self._receipt(context, status, started_epoch, started, final_hash)
            raise ProgrammaticRunError(str(error), receipt) from error
        except Exception as error:
            receipt = self._receipt(context, status, started_epoch, started, final_hash)
            raise ProgrammaticRunError(error.__class__.__name__, receipt) from error
        receipt = self._receipt(context, status, started_epoch, started, final_hash)
        return ProgrammaticRunResult(output=output, receipt=receipt)

    def _receipt(
        self,
        context: ProgrammaticExecutionContext,
        status: Literal["completed", "failed", "cancelled", "timed_out"],
        started_epoch: int,
        started_monotonic: float,
        final_hash: str | None,
    ) -> ProgrammaticRunReceipt:
        finished = int(time.time() * 1000)
        return ProgrammaticRunReceipt(
            schema="buddy.programmatic-tool-run.v1",
            provider="openai-agents-sdk",
            model=self.model,
            invocation_mode="programmatic_tool_call",
            trace_id=context.trace_id,
            status=status,
            started_at_unix_ms=started_epoch,
            finished_at_unix_ms=finished,
            elapsed_ms=int((time.monotonic() - started_monotonic) * 1000),
            tool_calls=context.receipts,
            final_output_sha256=final_hash,
            generated_code_retention=self.policy.generated_code_retention,
        )
