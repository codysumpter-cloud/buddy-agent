from buddy_agent.automations import AutomationJob, AutomationRegistry


def test_automation_registry_runs_job_now():
    registry = AutomationRegistry()
    registry.register(
        AutomationJob(
            name="check",
            description="Simple check.",
            schedule="manual",
            handler=lambda: "done",
        )
    )

    result = registry.run_now("check")

    assert registry.names() == ("check",)
    assert result.job_name == "check"
    assert result.output == "done"
