"""Provider-neutral checkpoint/restore contract for edge and hosted agent adapters."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from typing import Protocol


@dataclass(frozen=True)
class UsageTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    model_cost: float = 0.0
    tool_cost: float = 0.0

    def __add__(self, other: UsageTotals) -> UsageTotals:
        return UsageTotals(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            tool_calls=self.tool_calls + other.tool_calls,
            model_cost=self.model_cost + other.model_cost,
            tool_cost=self.tool_cost + other.tool_cost,
        )


@dataclass(frozen=True)
class RunCheckpoint:
    run_id: str
    cursor: int
    usage: UsageTotals
    trace_id: str
    hosted_multi_agent_enabled: bool = False
    metadata: dict[str, str] = field(default_factory=dict)

    def serialize(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @classmethod
    def restore(cls, payload: str) -> RunCheckpoint:
        value = json.loads(payload)
        value["usage"] = UsageTotals(**value["usage"])
        return cls(**value)


class CheckpointAdapter(Protocol):
    def start(self) -> RunCheckpoint: ...

    def execute_tool(self, state: RunCheckpoint) -> RunCheckpoint: ...

    def continue_run(self, state: RunCheckpoint) -> RunCheckpoint: ...

    def active_listener_count(self) -> int: ...

    def finish(self, state: RunCheckpoint) -> None: ...


class InMemoryCheckpointAdapter:
    """Reference adapter used to validate provider implementations and CI contracts."""

    def __init__(self) -> None:
        self._listeners = 0

    def start(self) -> RunCheckpoint:
        self._listeners += 1
        return RunCheckpoint(
            run_id="checkpoint-smoke",
            cursor=0,
            usage=UsageTotals(input_tokens=100, output_tokens=20, model_cost=0.01),
            trace_id="trace-smoke",
        )

    def execute_tool(self, state: RunCheckpoint) -> RunCheckpoint:
        return replace(
            state,
            cursor=state.cursor + 1,
            usage=state.usage + UsageTotals(tool_calls=1, tool_cost=0.002),
        )

    def continue_run(self, state: RunCheckpoint) -> RunCheckpoint:
        return replace(
            state,
            cursor=state.cursor + 1,
            usage=state.usage + UsageTotals(input_tokens=40, output_tokens=15, model_cost=0.005),
        )

    def active_listener_count(self) -> int:
        return self._listeners

    def finish(self, state: RunCheckpoint) -> None:
        del state
        self._listeners = max(0, self._listeners - 1)


@dataclass(frozen=True)
class CheckpointSmokeResult:
    usage_preserved: bool
    trace_preserved: bool
    listener_leak_free: bool
    final_usage: UsageTotals
    hosted_multi_agent_enabled: bool

    @property
    def ok(self) -> bool:
        return self.usage_preserved and self.trace_preserved and self.listener_leak_free


def run_checkpoint_smoke(adapter: CheckpointAdapter) -> CheckpointSmokeResult:
    started = adapter.start()
    after_tool = adapter.execute_tool(started)
    serialized = after_tool.serialize()
    restored = RunCheckpoint.restore(serialized)
    final = adapter.continue_run(restored)
    usage_preserved = final.usage == UsageTotals(
        input_tokens=140,
        output_tokens=35,
        tool_calls=1,
        model_cost=0.015,
        tool_cost=0.002,
    )
    trace_preserved = final.trace_id == started.trace_id and final.run_id == started.run_id
    adapter.finish(final)
    return CheckpointSmokeResult(
        usage_preserved=usage_preserved,
        trace_preserved=trace_preserved,
        listener_leak_free=adapter.active_listener_count() == 0,
        final_usage=final.usage,
        hosted_multi_agent_enabled=final.hosted_multi_agent_enabled,
    )
