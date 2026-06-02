from buddy_agent.runtime import BuddyActionLoopRuntime, requires_human_approval


def test_safe_worker_step_reports_back_to_buddy():
    loop = BuddyActionLoopRuntime()
    session = loop.start_session("Research a page and prepare a note")

    action = loop.delegate(
        title="Summarize Page",
        instruction="Prepare a concise page summary.",
        action_type="browser.summarize",
        risk="read-only",
    )
    report = loop.complete_action(action)

    assert session.status == "running"
    assert action.status == "delegated"
    assert action.assigned_agent_role == "worker"
    assert report.status == "step-completed"
    assert report.completed_action_ids == (action.id,)
    assert loop.receipts[0].status == "completed"
    assert loop.world_state.buddy_status == "continuing mission"
    assert loop.world_state.lil_buddy_status == "reported step complete"


def test_gated_step_pauses_for_buddy_review():
    loop = BuddyActionLoopRuntime()
    loop.start_session("Prepare a protected calendar update")

    action = loop.delegate(
        title="Review calendar update",
        instruction="Ask Buddy before applying this update.",
        action_type="calendar.create",
        risk="write",
    )

    assert action.status == "needs-review"
    assert action.risk == "write"
    assert loop.delegations[0].status == "blocked"
    assert loop.world_state.buddy_status == "approval needed"
    assert loop.world_state.lil_buddy_status == "paused"


def test_denied_gated_step_records_report_and_receipt():
    loop = BuddyActionLoopRuntime()
    loop.start_session("Prepare a protected calendar update")
    action = loop.delegate(
        title="Review calendar update",
        instruction="Ask Buddy before applying this update.",
        action_type="calendar.create",
        risk="write",
    )

    report = loop.deny_action(action)

    assert report.status == "needs-approval"
    assert report.produced_receipt_ids == (loop.receipts[0].id,)
    assert loop.receipts[0].status == "denied"
    assert loop.world_state.buddy_status == "replanning"
    assert loop.world_state.lil_buddy_status == "paused"


def test_policy_requires_review_only_for_write_in_safe_v1():
    assert requires_human_approval("read-only") is False
    assert requires_human_approval("draft-only") is False
    assert requires_human_approval("write") is True
