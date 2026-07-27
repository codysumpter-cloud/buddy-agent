"""Provider-neutral sandbox capability contract with conservative defaults."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal, Protocol

NetworkMode = Literal["none", "allowlist", "full"]
FilesystemMode = Literal["readonly", "workspace-write"]
SecretMode = Literal["none", "scoped"]
ApprovalMode = Literal["none", "on-request", "required"]


@dataclass(frozen=True)
class SandboxRequest:
    network: NetworkMode = "none"
    filesystem: FilesystemMode = "workspace-write"
    secrets: SecretMode = "none"
    timeout_seconds: int = 900
    network_allowlist: tuple[str, ...] = ()
    requires_human_approval: bool = False

    def __post_init__(self) -> None:
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
        if self.network == "allowlist" and not self.network_allowlist:
            raise ValueError("network_allowlist is required when network=allowlist")
        if self.network != "allowlist" and self.network_allowlist:
            raise ValueError("network_allowlist is only valid when network=allowlist")


@dataclass(frozen=True)
class SandboxCapabilities:
    provider: str
    network_none_enforced: bool
    network_allowlist_enforced: bool
    readonly_filesystem_enforced: bool
    workspace_write_enforced: bool
    scoped_secrets_supported: bool
    snapshots_supported: bool
    command_execution_supported: bool


@dataclass(frozen=True)
class SandboxPlan:
    provider: str
    request: SandboxRequest
    executable: bool
    missing_enforcement: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "request": asdict(self.request),
            "executable": self.executable,
            "missing_enforcement": list(self.missing_enforcement),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CommandRequest:
    argv: tuple[str, ...]
    cwd: str = "."
    timeout_seconds: int | None = None
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: int


@dataclass(frozen=True)
class SandboxSnapshot:
    snapshot_id: str


class Sandbox(Protocol):
    def exec(self, command: CommandRequest) -> CommandResult: ...

    def mount(self, files: tuple[tuple[str, str], ...]) -> None: ...

    def snapshot(self) -> SandboxSnapshot: ...

    def restore(self, snapshot_id: str) -> None: ...

    def destroy(self) -> None: ...


class SandboxProvider(Protocol):
    @property
    def capabilities(self) -> SandboxCapabilities: ...

    def plan(self, request: SandboxRequest) -> SandboxPlan: ...

    def create(self, request: SandboxRequest) -> Sandbox: ...


def plan_request(capabilities: SandboxCapabilities, request: SandboxRequest) -> SandboxPlan:
    missing: list[str] = []
    if request.network == "none" and not capabilities.network_none_enforced:
        missing.append("network:none")
    if request.network == "allowlist" and not capabilities.network_allowlist_enforced:
        missing.append("network:allowlist")
    if request.filesystem == "readonly" and not capabilities.readonly_filesystem_enforced:
        missing.append("filesystem:readonly")
    if request.filesystem == "workspace-write" and not capabilities.workspace_write_enforced:
        missing.append("filesystem:workspace-write")
    if request.secrets == "scoped" and not capabilities.scoped_secrets_supported:
        missing.append("secrets:scoped")
    if not capabilities.command_execution_supported:
        missing.append("command-execution")
    notes = []
    if request.requires_human_approval:
        notes.append("Human approval is required before provider creation or execution.")
    if request.network == "none":
        notes.append("Do not treat environment variables or prompt instructions as network isolation.")
    return SandboxPlan(
        provider=capabilities.provider,
        request=request,
        executable=not missing,
        missing_enforcement=tuple(missing),
        notes=tuple(notes),
    )


class PolicyOnlySandboxProvider:
    """Planning adapter used until a provider has a real audited execution implementation."""

    def __init__(self, capabilities: SandboxCapabilities) -> None:
        self._capabilities = capabilities

    @property
    def capabilities(self) -> SandboxCapabilities:
        return self._capabilities

    def plan(self, request: SandboxRequest) -> SandboxPlan:
        return plan_request(self.capabilities, request)

    def create(self, request: SandboxRequest) -> Sandbox:
        plan = self.plan(request)
        if request.requires_human_approval:
            raise PermissionError("sandbox creation requires explicit human approval")
        if not plan.executable:
            missing = ", ".join(plan.missing_enforcement)
            raise RuntimeError(f"provider cannot enforce requested sandbox contract: {missing}")
        raise NotImplementedError("policy-only provider cannot create a live sandbox")


PROFILES: dict[str, SandboxRequest] = {
    "coding": SandboxRequest(
        network="allowlist",
        network_allowlist=("api.github.com", "github.com", "registry.npmjs.org", "pypi.org"),
        filesystem="workspace-write",
        secrets="none",
        timeout_seconds=1800,
    ),
    "review": SandboxRequest(
        network="none",
        filesystem="readonly",
        secrets="none",
        timeout_seconds=900,
    ),
    "release": SandboxRequest(
        network="allowlist",
        network_allowlist=("api.github.com", "github.com"),
        filesystem="workspace-write",
        secrets="scoped",
        timeout_seconds=1800,
        requires_human_approval=True,
    ),
}


def profile(name: str) -> SandboxRequest:
    try:
        return PROFILES[name]
    except KeyError as error:
        raise ValueError(f"unknown sandbox profile: {name}") from error
