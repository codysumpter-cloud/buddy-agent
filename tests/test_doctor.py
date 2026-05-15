from buddy_agent.doctor import doctor_ok, run_doctor


def test_run_doctor_returns_passing_checks():
    checks = run_doctor()

    assert doctor_ok(checks) is True
    assert {check.name for check in checks} == {
        "runtime",
        "runtime-config",
        "buddy-brain-adapter",
        "omni-adapter",
        "app-bridge",
        "vault-provider",
        "companion-shell",
        "surface-parity",
        "integration-targets",
    }
