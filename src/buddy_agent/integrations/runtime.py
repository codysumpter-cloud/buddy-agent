"""Runtime helpers for Buddy integration targets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import IntegrationId, IntegrationStatus
from .targets import get_integration_target, integration_summary_lines


@dataclass(frozen=True)
class IntegrationRunResult:
    """Result returned by a Buddy integration runtime command."""

    ok: bool
    message: str
    detail: str = ""
    status: IntegrationStatus = "mapped"


class BuddyIntegrationRuntime:
    """Dependency-light runtime for Buddy-native integration capabilities."""

    def list_targets(self) -> tuple[str, ...]:
        """Return all integration target summary lines."""
        return integration_summary_lines()

    def describe(self, integration_id: IntegrationId) -> IntegrationRunResult:
        """Describe one integration target and its capability status."""
        target = get_integration_target(integration_id)
        lines = [
            f"{target.buddy_name} <- {target.upstream_repo}",
            f"license={target.upstream_license}",
            f"status={target.status}",
        ]
        for capability in target.capabilities:
            lines.append(
                f"- {capability.capability_id}: {capability.status} | "
                f"{capability.buddy_name}"
            )
        return IntegrationRunResult(
            ok=True,
            message="\n".join(lines),
            status=target.status,
        )

    def run(
        self,
        integration_id: IntegrationId,
        capability_id: str,
        *,
        path: str | Path | None = None,
    ) -> IntegrationRunResult:
        """Run one safe Buddy-native integration capability.

        Adapter-ready and mapped capabilities intentionally return explanatory results
        instead of pretending an upstream runtime has already been fully ported.
        """
        target = get_integration_target(integration_id)
        capability = target.get_capability(capability_id)

        if integration_id == "openmythos" and capability_id == "architecture-contract":
            return self._run_openmythos_architecture_contract()
        if integration_id == "symphony" and capability_id == "workflow-contract":
            return self._run_symphony_workflow_contract(path)

        return IntegrationRunResult(
            ok=False,
            message=(
                f"{integration_id}.{capability_id} is {capability.status}, not fully "
                "native-runtime in Buddy yet."
            ),
            detail=capability.validation,
            status=capability.status,
        )

    def _run_openmythos_architecture_contract(self) -> IntegrationRunResult:
        """Return a dependency-light OpenMythos architecture contract summary."""
        lines = (
            "Buddy Mythos architecture contract",
            "stages=prelude,recurrent_block,coda",
            "attention=gqa|mla",
            "ffn=moe_with_shared_experts",
            "loop_control=max_loop_iters,n_loops",
            "stability=lti_injection_spectral_radius_lt_1",
            "torch_backend=optional_not_default",
        )
        return IntegrationRunResult(
            ok=True,
            message="\n".join(lines),
            detail="OpenMythos PyTorch backend remains optional and adapter-ready.",
            status="native-runtime",
        )

    def _run_symphony_workflow_contract(
        self,
        path: str | Path | None,
    ) -> IntegrationRunResult:
        """Validate the minimal Symphony workflow front matter shape."""
        if path is None:
            return IntegrationRunResult(
                ok=True,
                message=(
                    "Buddy Symphony workflow contract ready: requires tracker, "
                    "workspace, hooks, agent, and codex sections when loaded from a file."
                ),
                detail="No workflow path provided; reported contract schema only.",
                status="native-runtime",
            )

        workflow_path = Path(path).expanduser()
        if not workflow_path.exists():
            return IntegrationRunResult(
                ok=False,
                message=f"Workflow file not found: {workflow_path}",
                status="native-runtime",
            )

        text = workflow_path.read_text(encoding="utf-8")
        front_matter = _extract_front_matter(text)
        missing = tuple(
            key
            for key in ("tracker:", "workspace:", "hooks:", "agent:", "codex:")
            if key not in front_matter
        )
        if missing:
            return IntegrationRunResult(
                ok=False,
                message="Symphony workflow contract invalid",
                detail="missing " + ", ".join(missing),
                status="native-runtime",
            )
        return IntegrationRunResult(
            ok=True,
            message="Symphony workflow contract valid",
            detail=str(workflow_path),
            status="native-runtime",
        )


def _extract_front_matter(text: str) -> str:
    """Extract Markdown YAML front matter without adding a YAML dependency."""
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return ""
    return parts[1]
