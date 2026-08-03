from pathlib import Path

import pytest

from buddy_agent.agent_readiness.local_container import (
    LocalContainerSandboxProvider,
    ProcessOutcome,
)
from buddy_agent.agent_readiness.sandbox import CommandRequest, SandboxRequest, profile


class FakeEngine:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.live: set[str] = set()
        self.next_exec = ProcessOutcome(0, "ok\n", "")

    def __call__(self, argv: tuple[str, ...], timeout_seconds: int | None) -> ProcessOutcome:
        self.calls.append(argv)
        if argv[1] == "version":
            return ProcessOutcome(0, "26.0\n", "")
        if argv[1] == "create":
            self.live.add("container-1")
            return ProcessOutcome(0, "container-1\n", "")
        if argv[1] == "start":
            return ProcessOutcome(0, argv[-1] + "\n", "")
        if argv[1] == "inspect":
            return ProcessOutcome(0 if argv[-1] in self.live else 1)
        if argv[1] == "rm":
            self.live.discard(argv[-1])
            return ProcessOutcome(0)
        if argv[1] == "exec":
            return self.next_exec
        return ProcessOutcome(1, "", "unexpected command")


def test_local_container_plan_is_truthful_about_allowlists(tmp_path: Path):
    provider = LocalContainerSandboxProvider(tmp_path, engine="docker", runner=FakeEngine())
    assert provider.plan(profile("review")).executable
    coding = provider.plan(profile("coding"))
    assert not coding.executable
    assert "network:allowlist" in coding.missing_enforcement


def test_local_container_create_uses_hardened_boundary(tmp_path: Path):
    engine = FakeEngine()
    provider = LocalContainerSandboxProvider(tmp_path, engine="docker", runner=engine)
    sandbox = provider.create(SandboxRequest(network="none", filesystem="readonly"))
    create = next(call for call in engine.calls if call[1] == "create")
    network_index = create.index("--network")
    assert create[network_index : network_index + 2] == ("--network", "none")
    assert "--cap-drop" in create
    assert "ALL" in create
    assert "no-new-privileges" in create
    mount = create[create.index("--mount") + 1]
    assert "dst=/workspace" in mount
    assert mount.endswith(",readonly")
    assert "/var/run/docker.sock" not in " ".join(create)
    sandbox.destroy()


def test_command_environment_rejects_secret_like_names(tmp_path: Path):
    engine = FakeEngine()
    provider = LocalContainerSandboxProvider(tmp_path, engine="docker", runner=engine)
    sandbox = provider.create(SandboxRequest(secrets="none"))
    with pytest.raises(PermissionError):
        sandbox.exec(CommandRequest(("true",), environment={"API_TOKEN": "nope"}))
    sandbox.destroy()


def test_timeout_destroys_entire_container(tmp_path: Path):
    engine = FakeEngine()
    provider = LocalContainerSandboxProvider(tmp_path, engine="docker", runner=engine)
    sandbox = provider.create(SandboxRequest())
    engine.next_exec = ProcessOutcome(124, "", "timed out", timed_out=True)
    result = sandbox.exec(CommandRequest(("sh", "-lc", "sleep 30"), timeout_seconds=1))
    assert result.exit_code == 124
    assert "container-1" not in engine.live
    with pytest.raises(RuntimeError, match="destroyed"):
        sandbox.exec(CommandRequest(("true",)))


def test_snapshot_restore_round_trip(tmp_path: Path):
    engine = FakeEngine()
    provider = LocalContainerSandboxProvider(tmp_path, engine="docker", runner=engine)
    sandbox = provider.create(SandboxRequest())
    target = tmp_path / "state.txt"
    target.write_text("before", encoding="utf-8")
    snapshot = sandbox.snapshot()
    target.write_text("after", encoding="utf-8")
    sandbox.restore(snapshot.snapshot_id)
    assert target.read_text(encoding="utf-8") == "before"
    sandbox.destroy()


def test_workspace_path_rejects_symlink_escape(tmp_path: Path):
    outside = tmp_path.parent / "outside-buddy-test"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "escape"
    link.symlink_to(outside, target_is_directory=True)
    engine = FakeEngine()
    provider = LocalContainerSandboxProvider(tmp_path, engine="docker", runner=engine)
    sandbox = provider.create(SandboxRequest())
    with pytest.raises(ValueError, match="outside"):
        sandbox.mount((("escape/leak.txt", "no"),))
    sandbox.destroy()
    link.unlink()
    outside.rmdir()
