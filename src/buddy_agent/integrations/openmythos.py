"""Buddy-native OpenMythos runtime contracts."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Literal

AttentionKind = Literal["gqa", "mla"]


@dataclass(frozen=True)
class BuddyMythosConfig:
    """Dependency-light Buddy-branded OpenMythos configuration."""

    name: str
    vocab_size: int = 32_000
    hidden_size: int = 512
    intermediate_size: int = 1_536
    num_hidden_layers: int = 8
    num_attention_heads: int = 8
    num_key_value_heads: int = 2
    num_experts: int = 4
    num_shared_experts: int = 1
    recurrent_depth: int = 4
    max_loop_iters: int = 8
    max_position_embeddings: int = 4_096
    attention_kind: AttentionKind = "gqa"
    lti_injection: bool = True
    spectral_radius: float = 0.97

    def validate(self) -> tuple[str, ...]:
        """Return config problems. Empty means the config is usable."""
        problems: list[str] = []
        if self.vocab_size <= 0:
            problems.append("vocab_size must be positive")
        if self.hidden_size <= 0:
            problems.append("hidden_size must be positive")
        if self.intermediate_size < self.hidden_size:
            problems.append("intermediate_size must be >= hidden_size")
        if self.num_hidden_layers <= 0:
            problems.append("num_hidden_layers must be positive")
        if self.num_attention_heads <= 0:
            problems.append("num_attention_heads must be positive")
        if self.hidden_size % self.num_attention_heads != 0:
            problems.append("hidden_size must be divisible by num_attention_heads")
        if self.num_key_value_heads <= 0:
            problems.append("num_key_value_heads must be positive")
        if self.num_attention_heads % self.num_key_value_heads != 0:
            problems.append("num_attention_heads must be divisible by num_key_value_heads")
        if self.num_experts < 1:
            problems.append("num_experts must be >= 1")
        if self.num_shared_experts < 0:
            problems.append("num_shared_experts must be >= 0")
        if self.recurrent_depth < 1:
            problems.append("recurrent_depth must be >= 1")
        if self.max_loop_iters < self.recurrent_depth:
            problems.append("max_loop_iters must be >= recurrent_depth")
        if self.attention_kind not in ("gqa", "mla"):
            problems.append("attention_kind must be gqa or mla")
        if not 0.0 < self.spectral_radius < 1.0:
            problems.append("spectral_radius must be > 0 and < 1")
        return tuple(problems)

    def parameter_estimate(self) -> int:
        """Return a rough parameter estimate for planning."""
        attention = self.num_hidden_layers * (4 * self.hidden_size * self.hidden_size)
        moe = self.num_hidden_layers * (
            self.num_experts + self.num_shared_experts
        ) * (2 * self.hidden_size * self.intermediate_size)
        recurrent = self.recurrent_depth * (self.hidden_size * self.hidden_size)
        embeddings = self.vocab_size * self.hidden_size
        return attention + moe + recurrent + embeddings

    def architecture_lines(self) -> tuple[str, ...]:
        """Return a stable CLI summary of the architecture."""
        problems = self.validate()
        status = "valid" if not problems else "invalid: " + "; ".join(problems)
        return (
            f"name={self.name}",
            "stages=prelude,recurrent_block,coda",
            f"attention={self.attention_kind}",
            f"heads={self.num_attention_heads}",
            f"kv_heads={self.num_key_value_heads}",
            f"ffn=moe experts={self.num_experts} shared={self.num_shared_experts}",
            "loop_control="
            f"recurrent_depth={self.recurrent_depth} max_loop_iters={self.max_loop_iters}",
            "lti_injection="
            f"{str(self.lti_injection).lower()} spectral_radius={self.spectral_radius}",
            f"estimated_params={self.parameter_estimate()}",
            f"validation={status}",
            f"torch_backend={torch_backend_status()}",
        )


VARIANT_CONFIGS: dict[str, BuddyMythosConfig] = {
    "buddy-mythos-tiny": BuddyMythosConfig(name="buddy-mythos-tiny"),
    "buddy-mythos-1b": BuddyMythosConfig(
        name="buddy-mythos-1b",
        hidden_size=2_048,
        intermediate_size=5_632,
        num_hidden_layers=16,
        num_attention_heads=16,
        num_key_value_heads=4,
        num_experts=8,
        recurrent_depth=6,
        max_loop_iters=12,
    ),
    "buddy-mythos-3b": BuddyMythosConfig(
        name="buddy-mythos-3b",
        hidden_size=2_560,
        intermediate_size=8_192,
        num_hidden_layers=24,
        num_attention_heads=20,
        num_key_value_heads=4,
        num_experts=8,
        recurrent_depth=8,
        max_loop_iters=16,
    ),
    "buddy-mythos-7b": BuddyMythosConfig(
        name="buddy-mythos-7b",
        hidden_size=4_096,
        intermediate_size=11_008,
        num_hidden_layers=32,
        num_attention_heads=32,
        num_key_value_heads=8,
        num_experts=8,
        recurrent_depth=8,
        max_loop_iters=16,
        attention_kind="mla",
    ),
}


def get_variant_config(name: str | None = None) -> BuddyMythosConfig:
    """Return a named Buddy Mythos config, defaulting to the tiny smoke model."""
    variant = (name or "buddy-mythos-tiny").strip() or "buddy-mythos-tiny"
    try:
        return VARIANT_CONFIGS[variant]
    except KeyError as error:
        supported = ", ".join(sorted(VARIANT_CONFIGS))
        message = f"Unknown Buddy Mythos variant {variant!r}. Supported: {supported}"
        raise ValueError(message) from error


def variant_summary_lines() -> tuple[str, ...]:
    """Return CLI-friendly variant summaries."""
    lines: list[str] = []
    for name in sorted(VARIANT_CONFIGS):
        config = VARIANT_CONFIGS[name]
        lines.append(
            f"{name}: hidden={config.hidden_size} layers={config.num_hidden_layers} "
            f"attention={config.attention_kind} recurrent_depth={config.recurrent_depth} "
            f"estimated_params={config.parameter_estimate()}"
        )
    return tuple(lines)


def torch_backend_status() -> str:
    """Return optional Torch backend availability without importing Torch."""
    has_torch = importlib.util.find_spec("torch") is not None
    return "available" if has_torch else "missing_optional_dependency"


def torch_backend_lines() -> tuple[str, ...]:
    """Return runtime lines for the optional OpenMythos Torch backend."""
    status = torch_backend_status()
    if status == "available":
        return (
            "torch_backend=available",
            "backend_import_guard=ok",
            "default_install=dependency_light",
        )
    return (
        "torch_backend=missing_optional_dependency",
        "install_hint=pip install -e .[mythos]",
        "backend_import_guard=ok",
    )


def training_plan_lines(variant: str | None = None) -> tuple[str, ...]:
    """Return a safe Buddy training plan instead of launching heavyweight training."""
    config = get_variant_config(variant)
    return (
        f"variant={config.name}",
        "dataset=text_stream_compatible",
        "launcher=explicit_run_only",
        "checkpoint_policy=allowlisted_path_required",
        "gpu_required=true_for_practical_runs",
        "default_action=plan_only_no_training_started",
    )
