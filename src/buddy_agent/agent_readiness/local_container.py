"""Auditable Docker/Podman sandbox adapter for Buddy readiness runs."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, cast

from .sandbox import (
    CommandRequest,
    CommandResult,
    SandboxCapabilities,
    SandboxPlan,
    SandboxRequest,
    SandboxSnapshot,
    plan_request,
)

ContainerEngine = Literal["docker", "podman"]
_CONTAINER_ENGINES: tuple[ContainerEngine, ...] = ("docker", "podman")
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SECRET_ENV_NAME = re.compile(
    r"(?:^|_)(?:API_KEY|TOKEN|SECRET|PASSWORD|PRIVATE_KEY|CREDENTIAL)(?:$|_)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProcessOutcome:
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


EngineRunner = Callable[[tuple[str, ...], int | None], ProcessOutcome]


@dataclass(frozen=True)
class SandboxSelfTestCheck:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxSelfTestResult:
    provider: str
    engine: str
    checks: tuple[SandboxSelfTestCheck, ...]

    @property
    def ok(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "engine": self.engine,
            "ok": self.ok,
            "checks": [check.to_dict() for check in self.checks],
        }


def _subprocess_runner(argv: tuple[str, ...], timeout_seconds: int | None) -> ProcessOutcome:
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else error.stdout
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else error.stderr
        return ProcessOutcome(124, stdout or "", stderr or "", timed_out=True)
    return ProcessOutcome(completed.returncode, completed.stdout, completed.stderr)


def _validate_environment(environment: dict[str, str], *, allow_secrets: bool) -> None:
    for key, value in environment.items():
        if not _ENV_NAME.fullmatch(key):
            raise ValueError(f"invalid environment variable name: {key!r}")
        if "\x00" in value:
            raise ValueError(f"environment variable contains a NUL byte: {key}")
        if not allow_secrets and _SECRET_ENV_NAME.search(key):
            raise PermissionError(f"secret-like environment variable is not allowed: {key}")


def _copy_workspace(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_symlink():
            target.symlink_to(os.readlink(child), target_is_directory=child.is_dir())
        elif child.is_dir():
            shutil.copytree(child, target, symlinks=True)
        else:
            shutil.copy2(child, target, follow_symlinks=False)


def _clear_workspace(workspace: Path) -> None:
    for child in workspace.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        else:
            shutil.rmtree(child)


class LocalContainerSandbox:
    """One isolated container bound to one explicit workspace."""

    def __init__(
        self,
        *,
        engine: ContainerEngine,
        container_id: str,
        workspace: Path,
        request: SandboxRequest,
        runner: EngineRunner,
    ) -> None:
        self.engine = engine
        self.container_id = container_id
        self.workspace = workspace.resolve()
        self.request = request
        self._runner = runner
        self._destroyed = False
        self._snapshot_root = Path(tempfile.mkdtemp(prefix="buddy-sandbox-snapshots-"))
        self._snapshots: dict[str, Path] = {}

    def _ensure_live(self) -> None:
        if self._destroyed:
            raise RuntimeError("sandbox has been destroyed")

    def _workspace_path(self, relative: str, *, must_exist: bool = False) -> Path:
        posix = PurePosixPath(relative)
        if posix.is_absolute() or ".." in posix.parts:
            raise ValueError("sandbox paths must stay within the workspace")
        candidate = (self.workspace / Path(*posix.parts)).resolve(strict=must_exist)
        try:
            candidate.relative_to(self.workspace)
        except ValueError as error:
            raise ValueError("sandbox path resolves outside the workspace") from error
        return candidate

    def exec(self, command: CommandRequest) -> CommandResult:
        self._ensure_live()
        if not command.argv or any(not part or "\x00" in part for part in command.argv):
            raise ValueError("argv must contain non-empty, NUL-free arguments")
        _validate_environment(command.environment, allow_secrets=self.request.secrets == "scoped")
        cwd = self._workspace_path(command.cwd, must_exist=True)
        relative_cwd = cwd.relative_to(self.workspace).as_posix()
        container_cwd = "/workspace" if relative_cwd == "." else f"/workspace/{relative_cwd}"
        timeout = command.timeout_seconds or self.request.timeout_seconds
        if timeout < 1:
            raise ValueError("timeout_seconds must be positive")
        timeout = min(timeout, self.request.timeout_seconds)
        argv: list[str] = [self.engine, "exec", "--workdir", container_cwd]
        for key, value in sorted(command.environment.items()):
            argv.extend(("--env", f"{key}={value}"))
        argv.append(self.container_id)
        argv.extend(command.argv)
        started = time.monotonic()
        outcome = self._runner(tuple(argv), timeout)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if outcome.timed_out:
            self.destroy()
            stderr = outcome.stderr or "command timed out; container was destroyed"
            return CommandResult(124, outcome.stdout, stderr, elapsed_ms)
        return CommandResult(outcome.exit_code, outcome.stdout, outcome.stderr, elapsed_ms)

    def mount(self, files: tuple[tuple[str, str], ...]) -> None:
        self._ensure_live()
        if self.request.filesystem != "workspace-write":
            raise PermissionError("cannot mount files into a readonly workspace")
        for relative, content in files:
            destination = self._workspace_path(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    def snapshot(self) -> SandboxSnapshot:
        self._ensure_live()
        snapshot_id = uuid.uuid4().hex
        destination = self._snapshot_root / snapshot_id
        _copy_workspace(self.workspace, destination)
        self._snapshots[snapshot_id] = destination
        return SandboxSnapshot(snapshot_id)

    def restore(self, snapshot_id: str) -> None:
        self._ensure_live()
        try:
            source = self._snapshots[snapshot_id]
        except KeyError as error:
            raise ValueError(f"unknown snapshot: {snapshot_id}") from error
        _clear_workspace(self.workspace)
        for child in source.iterdir():
            target = self.workspace / child.name
            if child.is_symlink():
                target.symlink_to(os.readlink(child), target_is_directory=child.is_dir())
            elif child.is_dir():
                shutil.copytree(child, target, symlinks=True)
            else:
                shutil.copy2(child, target, follow_symlinks=False)

    def destroy(self) -> None:
        if self._destroyed:
            return
        self._runner((self.engine, "rm", "--force", self.container_id), 30)
        self._destroyed = True
        shutil.rmtree(self._snapshot_root, ignore_errors=True)


class LocalContainerSandboxProvider:
    """Docker/Podman adapter with explicit mounts and no implicit host secrets."""

    def __init__(
        self,
        workspace: Path,
        *,
        image: str = "python:3.12-slim",
        engine: ContainerEngine | None = None,
        scoped_secrets: dict[str, str] | None = None,
        runner: EngineRunner = _subprocess_runner,
    ) -> None:
        self.workspace = workspace.expanduser().resolve()
        self.image = image.strip()
        self._requested_engine = engine
        self._runner = runner
        self.scoped_secrets = dict(scoped_secrets or {})
        if not self.image:
            raise ValueError("container image is required")
        _validate_environment(self.scoped_secrets, allow_secrets=True)

    @property
    def capabilities(self) -> SandboxCapabilities:
        return SandboxCapabilities(
            provider="local-container",
            network_none_enforced=True,
            network_allowlist_enforced=False,
            readonly_filesystem_enforced=True,
            workspace_write_enforced=True,
            scoped_secrets_supported=True,
            snapshots_supported=True,
            command_execution_supported=True,
        )

    def plan(self, request: SandboxRequest) -> SandboxPlan:
        plan = plan_request(self.capabilities, request)
        notes = list(plan.notes)
        notes.append("Hostname allowlists are denied until an audited network proxy exists.")
        notes.append("The provider never mounts the engine socket or inherits host secrets.")
        return SandboxPlan(
            provider=plan.provider,
            request=plan.request,
            executable=plan.executable,
            missing_enforcement=plan.missing_enforcement,
            notes=tuple(notes),
        )

    def _resolve_engine(self) -> ContainerEngine:
        candidates: Sequence[ContainerEngine]
        if self._requested_engine is not None:
            candidates = (self._requested_engine,)
        else:
            candidates = tuple(
                engine for engine in _CONTAINER_ENGINES if shutil.which(engine) is not None
            )
        for engine in candidates:
            outcome = self._runner((engine, "version", "--format", "{{.Server.Version}}"), 15)
            if outcome.exit_code == 0 and not outcome.timed_out:
                return engine
        requested = self._requested_engine or "docker or podman"
        raise RuntimeError(f"no healthy local container engine found: {requested}")

    def _create_environment_file(self, request: SandboxRequest) -> str | None:
        if request.secrets == "none":
            return None
        if not self.scoped_secrets:
            raise RuntimeError("secrets=scoped requires explicitly supplied scoped_secrets")
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="buddy-sandbox-env-",
            delete=False,
        )
        try:
            os.chmod(handle.name, 0o600)
            for key, value in sorted(self.scoped_secrets.items()):
                if "\n" in value or "\r" in value:
                    raise ValueError(f"multiline secrets are not supported: {key}")
                handle.write(f"{key}={value}\n")
        finally:
            handle.close()
        return handle.name

    def create(self, request: SandboxRequest) -> LocalContainerSandbox:
        if request.requires_human_approval:
            raise PermissionError("sandbox creation requires explicit human approval")
        plan = self.plan(request)
        if not plan.executable:
            missing = ", ".join(plan.missing_enforcement)
            raise RuntimeError(f"provider cannot enforce requested sandbox contract: {missing}")
        if not self.workspace.is_dir():
            raise FileNotFoundError(f"workspace does not exist: {self.workspace}")
        if "," in str(self.workspace):
            raise ValueError("workspace paths containing commas are not supported by --mount")
        engine = self._resolve_engine()
        name = f"buddy-sandbox-{uuid.uuid4().hex[:12]}"
        mount = f"type=bind,src={self.workspace},dst=/workspace"
        if request.filesystem == "readonly":
            mount += ",readonly"
        argv: list[str] = [
            engine,
            "create",
            "--name",
            name,
            "--label",
            "io.prismtek.buddy.sandbox=true",
            "--workdir",
            "/workspace",
            "--mount",
            mount,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "256",
            "--memory",
            "1g",
            "--cpus",
            "2",
        ]
        if os.name == "posix":
            argv.extend(("--user", f"{os.getuid()}:{os.getgid()}"))
        if request.network == "none":
            argv.extend(("--network", "none"))
        environment_file = self._create_environment_file(request)
        if environment_file is not None:
            argv.extend(("--env-file", environment_file))
        argv.extend((self.image, "sh", "-lc", "exec sleep infinity"))
        try:
            created = self._runner(tuple(argv), 120)
        finally:
            if environment_file is not None:
                Path(environment_file).unlink(missing_ok=True)
        if created.exit_code != 0 or created.timed_out:
            detail = created.stderr.strip() or "container create failed"
            raise RuntimeError(detail)
        container_id = created.stdout.strip() or name
        started = self._runner((engine, "start", container_id), 60)
        if started.exit_code != 0 or started.timed_out:
            self._runner((engine, "rm", "--force", container_id), 30)
            detail = started.stderr.strip() or "container start failed"
            raise RuntimeError(detail)
        return LocalContainerSandbox(
            engine=engine,
            container_id=container_id,
            workspace=self.workspace,
            request=request,
            runner=self._runner,
        )

    def container_exists(self, engine: ContainerEngine, container_id: str) -> bool:
        outcome = self._runner((engine, "inspect", container_id), 30)
        return outcome.exit_code == 0 and not outcome.timed_out

    def self_test(self) -> SandboxSelfTestResult:
        checks: list[SandboxSelfTestCheck] = []
        request = SandboxRequest(
            network="none",
            filesystem="workspace-write",
            secrets="none",
            timeout_seconds=20,
        )
        previous = os.environ.get("BUDDY_HOST_SECRET_SENTINEL")
        os.environ["BUDDY_HOST_SECRET_SENTINEL"] = "must-not-enter-container"
        engine_name = self._requested_engine or "auto"
        try:
            with tempfile.TemporaryDirectory(
                prefix=".buddy-sandbox-self-test-", dir=self.workspace
            ) as temporary_workspace:
                probe_provider = LocalContainerSandboxProvider(
                    Path(temporary_workspace),
                    image=self.image,
                    engine=self._requested_engine,
                    runner=self._runner,
                )
                sandbox = probe_provider.create(request)
                engine_name = sandbox.engine
                try:
                    probe = sandbox.exec(
                        CommandRequest(
                            argv=(
                                "python",
                                "-c",
                                (
                                    "import json,os,pathlib,socket;"
                                    "p=pathlib.Path('/workspace/state.txt');"
                                    "p.write_text('original', encoding='utf-8');"
                                    "secret=os.getenv('BUDDY_HOST_SECRET_SENTINEL');"
                                    "network='open';"
                                    "\ntry:\n socket.create_connection(('1.1.1.1',53),1)\n"
                                    "except OSError:\n network='blocked'\n"
                                    "print(json.dumps({'secret':secret,'network':network,"
                                    "'write':p.read_text()}))"
                                ),
                            ),
                            timeout_seconds=10,
                        )
                    )
                    payload = cast(
                        dict[str, object],
                        json.loads(probe.stdout.strip()) if probe.exit_code == 0 else {},
                    )
                    checks.append(
                        SandboxSelfTestCheck(
                            "command_execution", probe.exit_code == 0, probe.stderr.strip()
                        )
                    )
                    checks.append(
                        SandboxSelfTestCheck(
                            "network_none",
                            payload.get("network") == "blocked",
                            f"reported={payload.get('network')!r}",
                        )
                    )
                    checks.append(
                        SandboxSelfTestCheck(
                            "host_secret_absent",
                            payload.get("secret") is None,
                            (
                                "host sentinel was not inherited"
                                if payload.get("secret") is None
                                else "host sentinel leaked"
                            ),
                        )
                    )
                    test_file = Path(temporary_workspace) / "state.txt"
                    checks.append(
                        SandboxSelfTestCheck(
                            "workspace_mount_scoped",
                            test_file.is_file()
                            and test_file.read_text(encoding="utf-8") == "original",
                            str(test_file),
                        )
                    )
                    snapshot = sandbox.snapshot()
                    sandbox.exec(
                        CommandRequest(
                            (
                                "python",
                                "-c",
                                "open('/workspace/state.txt','w').write('changed')",
                            )
                        )
                    )
                    sandbox.restore(snapshot.snapshot_id)
                    checks.append(
                        SandboxSelfTestCheck(
                            "checkpoint_restore",
                            test_file.read_text(encoding="utf-8") == "original",
                            snapshot.snapshot_id,
                        )
                    )
                    engine = sandbox.engine
                    container_id = sandbox.container_id
                finally:
                    sandbox.destroy()
                checks.append(
                    SandboxSelfTestCheck(
                        "lifecycle_cleanup",
                        not probe_provider.container_exists(engine, container_id),
                        container_id,
                    )
                )

                timeout_sandbox = probe_provider.create(request)
                timeout_engine = timeout_sandbox.engine
                timeout_container_id = timeout_sandbox.container_id
                timed = timeout_sandbox.exec(
                    CommandRequest(("sh", "-lc", "sleep 30 & wait"), timeout_seconds=1)
                )
                checks.append(
                    SandboxSelfTestCheck(
                        "timeout_process_tree_terminated",
                        timed.exit_code == 124
                        and not probe_provider.container_exists(
                            timeout_engine, timeout_container_id
                        ),
                        timed.stderr.strip(),
                    )
                )
        except Exception as error:  # pragma: no cover - returned as self-test evidence
            checks.append(SandboxSelfTestCheck("unexpected_error", False, str(error)))
        finally:
            if previous is None:
                os.environ.pop("BUDDY_HOST_SECRET_SENTINEL", None)
            else:
                os.environ["BUDDY_HOST_SECRET_SENTINEL"] = previous
        return SandboxSelfTestResult("local-container", engine_name, tuple(checks))
