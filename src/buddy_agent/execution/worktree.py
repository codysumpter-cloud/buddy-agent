"""Approval-bound repository execution in an isolated git worktree.

This is a real repository executor, not a host sandbox. It isolates repository
mutation in a dedicated worktree and strips inherited secrets, but a child process
can still access the host filesystem and network if the operating system allows it.
Those limitations are emitted in every capability/evidence record.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from buddy_agent.tasks import TaskStore, TaskStoreError

MAX_OUTPUT_BYTES = 256_000
SAFE_ENV_KEYS = {"PATH", "LANG", "LC_ALL", "SYSTEMROOT", "WINDIR"}
ALLOWED_EXECUTABLES = {
    "cargo",
    "go",
    "make",
    "mypy",
    "node",
    "npm",
    "npx",
    "pnpm",
    "python",
    "python3",
    "pytest",
    "ruff",
    "yarn",
}
ALLOWED_GIT_SUBCOMMANDS = {"diff", "log", "rev-parse", "show", "status"}
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|private[_-]?key)\s*[:=]\s*([^\s]+)"
)
TASK_ID_PATTERN = re.compile(r"^task-[a-f0-9]{24}$")


class WorktreeExecutionError(ValueError):
    """Safe worktree execution failure."""


@dataclass(frozen=True)
class CommandSpec:
    """One direct, no-shell command in the worktree."""

    argv: tuple[str, ...]
    cwd: str = "."
    timeout_seconds: int = 900

    def __post_init__(self) -> None:
        if not self.argv or not self.argv[0].strip():
            raise WorktreeExecutionError("command argv cannot be empty")
        if self.timeout_seconds < 1 or self.timeout_seconds > 3600:
            raise WorktreeExecutionError("command timeout must be between 1 and 3600 seconds")


@dataclass(frozen=True)
class WorktreeRequest:
    """Reviewed execution plan for one approved task."""

    task_id: str
    repository: Path
    commands: tuple[CommandSpec, ...]
    base_ref: str = "HEAD"
    branch_name: str | None = None
    keep_worktree: bool = True

    def __post_init__(self) -> None:
        if not TASK_ID_PATTERN.fullmatch(self.task_id):
            raise WorktreeExecutionError("invalid Buddy task id")
        if not self.commands:
            raise WorktreeExecutionError("execution request must include at least one command")
        if not self.base_ref.strip() or self.base_ref.startswith("-"):
            raise WorktreeExecutionError("invalid git base ref")


@dataclass(frozen=True)
class CommandEvidence:
    argv: tuple[str, ...]
    cwd: str
    exit_code: int
    elapsed_ms: int
    stdout_path: str
    stderr_path: str
    stdout_sha256: str
    stderr_sha256: str
    truncated: bool


@dataclass
class WorktreeEvidence:
    """Machine-readable evidence for one worktree execution."""

    schema: str
    task_id: str
    repository: str
    worktree: str
    branch: str
    base_ref: str
    head_before: str
    head_after: str
    status: str
    started_at_unix_ms: int
    finished_at_unix_ms: int
    commands: list[CommandEvidence] = field(default_factory=list)
    git_status_path: str = ""
    diff_path: str = ""
    diff_stat_path: str = ""
    capabilities: dict[str, bool] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["commands"] = [asdict(command) for command in self.commands]
        return value


class GitWorktreeExecutor:
    """Execute allowlisted commands inside an approval-bound git worktree."""

    def __init__(
        self,
        task_store: TaskStore,
        *,
        worktree_root: Path | None = None,
        evidence_root: Path | None = None,
    ) -> None:
        self.task_store = task_store
        self.worktree_root = (worktree_root or Path("~/.buddy_agent/worktrees")).expanduser().resolve()
        self.evidence_root = (evidence_root or Path("~/.buddy_agent/executions")).expanduser().resolve()

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "repository_worktree_isolation": True,
            "direct_no_shell_execution": True,
            "inherited_secret_environment_removed": True,
            "command_allowlist_enforced": True,
            "cwd_scoped_to_worktree": True,
            "host_filesystem_isolation": False,
            "network_isolation": False,
            "scoped_secrets_supported": False,
        }

    def _run_git(
        self,
        repository: Path,
        argv: tuple[str, ...],
        *,
        timeout: int = 120,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ("git", "-C", str(repository), *argv),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=self._environment(repository / ".buddy-home"),
        )
        if check and result.returncode != 0:
            message = self._redact(result.stderr.strip() or result.stdout.strip())
            raise WorktreeExecutionError(f"git command failed: {message[:1000]}")
        return result

    def _repository(self, value: Path) -> Path:
        repository = value.expanduser().resolve()
        if not repository.is_dir():
            raise WorktreeExecutionError("repository path is not a directory")
        result = self._run_git(repository, ("rev-parse", "--show-toplevel"))
        root = Path(result.stdout.strip()).resolve()
        if root != repository:
            raise WorktreeExecutionError("repository path must be the git top-level directory")
        return root

    def _task(self, task_id: str) -> None:
        try:
            task = self.task_store.load(task_id)
        except TaskStoreError as error:
            raise WorktreeExecutionError(str(error)) from error
        if task.status != "running":
            raise WorktreeExecutionError("task must be running before repository execution")
        if task.approval.required and task.approval.decision != "approved":
            raise WorktreeExecutionError("task execution requires recorded human approval")

    def _branch(self, request: WorktreeRequest) -> str:
        branch = request.branch_name or f"buddy/{request.task_id}"
        if branch.startswith("-") or not re.fullmatch(r"[A-Za-z0-9._/-]{1,180}", branch):
            raise WorktreeExecutionError("invalid worktree branch name")
        if ".." in branch or "//" in branch or branch.endswith(("/", ".")):
            raise WorktreeExecutionError("invalid worktree branch name")
        return branch

    def _environment(self, home: Path) -> dict[str, str]:
        environment = {key: value for key, value in os.environ.items() if key in SAFE_ENV_KEYS}
        environment.update(
            {
                "HOME": str(home),
                "CI": "true",
                "NO_COLOR": "1",
                "GIT_TERMINAL_PROMPT": "0",
                "PYTHONUNBUFFERED": "1",
            }
        )
        return environment

    def _redact(self, text: str) -> str:
        return SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=[REDACTED]", text)

    def _write_output(self, path: Path, value: str) -> tuple[str, bool]:
        redacted = self._redact(value)
        encoded = redacted.encode("utf-8", errors="replace")
        truncated = len(encoded) > MAX_OUTPUT_BYTES
        if truncated:
            encoded = encoded[:MAX_OUTPUT_BYTES] + b"\n[TRUNCATED]\n"
        path.write_bytes(encoded)
        return hashlib.sha256(encoded).hexdigest(), truncated

    def _safe_cwd(self, worktree: Path, relative: str) -> Path:
        if Path(relative).is_absolute():
            raise WorktreeExecutionError("command cwd must be relative to the worktree")
        resolved = (worktree / relative).resolve()
        try:
            resolved.relative_to(worktree)
        except ValueError as error:
            raise WorktreeExecutionError("command cwd escapes the worktree") from error
        if not resolved.is_dir():
            raise WorktreeExecutionError(f"command cwd does not exist: {relative}")
        return resolved

    def _validate_command(self, spec: CommandSpec) -> None:
        executable = Path(spec.argv[0]).name
        if executable == "git":
            if len(spec.argv) < 2 or spec.argv[1] not in ALLOWED_GIT_SUBCOMMANDS:
                raise WorktreeExecutionError("git command is not in the read-only execution allowlist")
            return
        if executable not in ALLOWED_EXECUTABLES:
            raise WorktreeExecutionError(f"executable is not allowlisted: {executable}")

    def prepare(self, request: WorktreeRequest) -> tuple[Path, str, str]:
        """Create a dedicated branch/worktree after validating task approval."""
        self._task(request.task_id)
        repository = self._repository(request.repository)
        branch = self._branch(request)
        worktree = self.worktree_root / request.task_id
        if worktree.exists():
            raise WorktreeExecutionError(f"worktree already exists: {worktree}")
        branch_exists = self._run_git(
            repository,
            ("show-ref", "--verify", "--quiet", f"refs/heads/{branch}"),
            check=False,
        )
        if branch_exists.returncode == 0:
            raise WorktreeExecutionError(f"worktree branch already exists: {branch}")
        self.worktree_root.mkdir(parents=True, exist_ok=True)
        self._run_git(repository, ("worktree", "add", "-b", branch, str(worktree), request.base_ref))
        head = self._run_git(worktree, ("rev-parse", "HEAD")).stdout.strip()
        (worktree / ".buddy-home").mkdir(parents=True, exist_ok=True)
        return worktree, branch, head

    def execute(self, request: WorktreeRequest) -> WorktreeEvidence:
        """Run the reviewed commands and persist sanitized evidence."""
        repository = self._repository(request.repository)
        worktree, branch, head_before = self.prepare(request)
        evidence_dir = self.evidence_root / request.task_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        started = int(time.time() * 1000)
        evidence = WorktreeEvidence(
            schema="buddy.worktree-execution.v1",
            task_id=request.task_id,
            repository=str(repository),
            worktree=str(worktree),
            branch=branch,
            base_ref=request.base_ref,
            head_before=head_before,
            head_after=head_before,
            status="running",
            started_at_unix_ms=started,
            finished_at_unix_ms=started,
            capabilities=self.capabilities,
            limitations=[
                "Repository mutation is isolated in a git worktree, not an OS/container sandbox.",
                "Host filesystem access is not technically blocked by this executor.",
                "Network access is not technically blocked by this executor.",
                "No secret environment variables are intentionally inherited or injected.",
            ],
        )
        try:
            for index, spec in enumerate(request.commands, start=1):
                self._validate_command(spec)
                cwd = self._safe_cwd(worktree, spec.cwd)
                command_started = time.monotonic()
                try:
                    result = subprocess.run(
                        spec.argv,
                        cwd=cwd,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=spec.timeout_seconds,
                        check=False,
                        shell=False,
                        env=self._environment(worktree / ".buddy-home"),
                    )
                    exit_code = result.returncode
                    stdout = result.stdout
                    stderr = result.stderr
                except subprocess.TimeoutExpired as error:
                    exit_code = 124
                    stdout = str(error.stdout or "")
                    stderr = f"command timed out after {spec.timeout_seconds} seconds\n{error.stderr or ''}"
                elapsed_ms = int((time.monotonic() - command_started) * 1000)
                stdout_path = evidence_dir / f"command-{index:02d}.stdout.log"
                stderr_path = evidence_dir / f"command-{index:02d}.stderr.log"
                stdout_sha, stdout_truncated = self._write_output(stdout_path, stdout)
                stderr_sha, stderr_truncated = self._write_output(stderr_path, stderr)
                evidence.commands.append(
                    CommandEvidence(
                        argv=spec.argv,
                        cwd=str(cwd.relative_to(worktree)) or ".",
                        exit_code=exit_code,
                        elapsed_ms=elapsed_ms,
                        stdout_path=str(stdout_path),
                        stderr_path=str(stderr_path),
                        stdout_sha256=stdout_sha,
                        stderr_sha256=stderr_sha,
                        truncated=stdout_truncated or stderr_truncated,
                    )
                )
                if exit_code != 0:
                    raise WorktreeExecutionError(
                        f"command {index} failed with exit code {exit_code}: {Path(spec.argv[0]).name}"
                    )
            evidence.status = "completed"
        except (OSError, WorktreeExecutionError) as error:
            evidence.status = "failed"
            evidence.error = self._redact(str(error))[:2000]
        finally:
            status = self._run_git(worktree, ("status", "--short"), check=False)
            diff = self._run_git(worktree, ("diff", "--binary", "HEAD"), check=False)
            stat = self._run_git(worktree, ("diff", "--stat", "HEAD"), check=False)
            status_path = evidence_dir / "git-status.txt"
            diff_path = evidence_dir / "changes.patch"
            stat_path = evidence_dir / "diff-stat.txt"
            self._write_output(status_path, status.stdout + status.stderr)
            self._write_output(diff_path, diff.stdout + diff.stderr)
            self._write_output(stat_path, stat.stdout + stat.stderr)
            evidence.git_status_path = str(status_path)
            evidence.diff_path = str(diff_path)
            evidence.diff_stat_path = str(stat_path)
            evidence.head_after = self._run_git(worktree, ("rev-parse", "HEAD")).stdout.strip()
            evidence.finished_at_unix_ms = int(time.time() * 1000)
            evidence_path = evidence_dir / "execution-evidence.json"
            evidence_path.write_text(json.dumps(evidence.to_dict(), indent=2, sort_keys=True) + "\n")
            if not request.keep_worktree and evidence.status == "completed":
                self.cleanup(repository, request.task_id, delete_branch=False)
        return evidence

    def cleanup(self, repository: Path, task_id: str, *, delete_branch: bool = False) -> None:
        """Remove one known worktree; branch deletion remains explicit."""
        if not TASK_ID_PATTERN.fullmatch(task_id):
            raise WorktreeExecutionError("invalid Buddy task id")
        root = self._repository(repository)
        worktree = self.worktree_root / task_id
        if worktree.exists():
            self._run_git(root, ("worktree", "remove", "--force", str(worktree)))
        self._run_git(root, ("worktree", "prune"), check=False)
        if delete_branch:
            branch = f"buddy/{task_id}"
            self._run_git(root, ("branch", "-D", branch), check=False)
        if worktree.exists():
            shutil.rmtree(worktree)
