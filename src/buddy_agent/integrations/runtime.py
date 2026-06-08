"""Runtime helpers for Buddy integration targets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import IntegrationId, IntegrationStatus
from .openmythos import (
    get_variant_config,
    torch_backend_lines,
    training_plan_lines,
    variant_summary_lines,
)
from .symphony import (
    local_tracker_lines,
    observability_lines,
    work_runner_lines,
    worker_bridge_lines,
    workflow_contract_lines,
    workspace_plan_lines,
)
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
        return IntegrationRunResult(ok=True, message="\n".join(lines), status=target.status)

    def run(
        self,
        integration_id: IntegrationId,
        capability_id: str,
        *,
        path: str | Path | None = None,
    ) -> IntegrationRunResult:
        """Run one safe Buddy-native integration capability."""
        get_integration_target(integration_id).get_capability(capability_id)
        if integration_id == "openmythos":
            return self._run_openmythos(capability_id, path)
        if integration_id == "symphony":
            return self._run_symphony(capability_id, path)
        return self._not_runnable(integration_id, capability_id)

    def _run_openmythos(
        self,
        capability_id: str,
        path: str | Path | None,
    ) -> IntegrationRunResult:
        try:
            return self._run_openmythos_checked(capability_id, path)
        except ValueError as error:
            return IntegrationRunResult(
                ok=False,
                message=str(error),
                status="native-runtime",
            )

    def _run_openmythos_checked(
        self,
        capability_id: str,
        path: str | Path | None,
    ) -> IntegrationRunResult:
        variant = str(path) if path is not None else None
        if capability_id == "architecture-contract":
            config = get_variant_config(variant)
            return IntegrationRunResult(
                ok=not config.validate(),
                message="\n".join(config.architecture_lines()),
                detail="Buddy Mythos architecture contract is dependency-light and testable.",
                status="native-runtime",
            )
        if capability_id == "variant-configs":
            return IntegrationRunResult(
                ok=True,
                message="\n".join(variant_summary_lines()),
                status="native-runtime",
            )
        if capability_id == "torch-model":
            return IntegrationRunResult(
                ok=True,
                message="\n".join(torch_backend_lines()),
                detail="Model construction is optional; default install stays light.",
                status="adapter-ready",
            )
        if capability_id == "training-script":
            return IntegrationRunResult(
                ok=True,
                message="\n".join(training_plan_lines(variant)),
                detail="Training is planned but not started by default.",
                status="native-runtime",
            )
        return self._not_runnable("openmythos", capability_id)

    def _run_symphony(
        self,
        capability_id: str,
        path: str | Path | None,
    ) -> IntegrationRunResult:
        try:
            return self._run_symphony_checked(capability_id, path)
        except (FileNotFoundError, ValueError) as error:
            return IntegrationRunResult(
                ok=False,
                message=str(error),
                status="native-runtime",
            )

    def _run_symphony_checked(
        self,
        capability_id: str,
        path: str | Path | None,
    ) -> IntegrationRunResult:
        if capability_id == "workflow-contract":
            lines = workflow_contract_lines(path)
            ok = not any("invalid" in line for line in lines)
            return IntegrationRunResult(ok=ok, message="\n".join(lines), status="native-runtime")
        if capability_id == "tracker-local":
            return IntegrationRunResult(
                ok=True,
                message="\n".join(local_tracker_lines(path)),
                status="native-runtime",
            )
        if capability_id == "workspace-spawn":
            if path is None:
                return IntegrationRunResult(
                    ok=False,
                    message="workspace-spawn requires a WORKFLOW.md path",
                    status="native-runtime",
                )
            return IntegrationRunResult(
                ok=True,
                message="\n".join(workspace_plan_lines(path)),
                detail="Plan only. Use work-runner to create local files.",
                status="native-runtime",
            )
        if capability_id == "work-runner":
            if path is None:
                return IntegrationRunResult(
                    ok=False,
                    message="work-runner requires a WORKFLOW.md path",
                    status="native-runtime",
                )
            return IntegrationRunResult(
                ok=True,
                message="\n".join(work_runner_lines(path)),
                detail="Local workspace files created.",
                status="native-runtime",
            )
        if capability_id == "codex-app-server":
            return IntegrationRunResult(
                ok=True,
                message="\n".join(worker_bridge_lines()),
                detail="Buddy exposes the bridge contract without starting a process.",
                status="adapter-ready",
            )
        if capability_id == "observability":
            return IntegrationRunResult(
                ok=True,
                message="\n".join(observability_lines()),
                status="native-runtime",
            )
        return self._not_runnable("symphony", capability_id)

    def _not_runnable(self, integration_id: IntegrationId, capability_id: str) -> IntegrationRunResult:
        target = get_integration_target(integration_id)
        capability = target.get_capability(capability_id)
        return IntegrationRunResult(
            ok=False,
            message=f"{integration_id}.{capability_id} is {capability.status} in Buddy.",
            detail=capability.validation,
            status=capability.status,
        )
