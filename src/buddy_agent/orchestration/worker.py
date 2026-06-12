"""Lil' Buddy worker scaffold for scoped local execution."""

from __future__ import annotations

from dataclasses import dataclass

from .envelopes import ResultEnvelope, TaskEnvelope


@dataclass(frozen=True)
class LilBuddyWorker:
    """A constrained worker that executes only a Buddy task envelope."""

    name: str = "Lil' Buddy"

    def execute(self, task: TaskEnvelope) -> ResultEnvelope:
        """Execute the delegated scope and return a structured result envelope."""
        if task.worker != self.name:
            return ResultEnvelope(
                task_id=task.task_id,
                worker=self.name,
                status="blocked",
                summary="Task envelope was assigned to a different worker.",
                risks=(f"Envelope worker was {task.worker!r}, not {self.name!r}.",),
                open_questions=("Should Buddy reissue this task to the correct worker?",),
            )
        if not task.review_required:
            return ResultEnvelope(
                task_id=task.task_id,
                worker=self.name,
                status="blocked",
                summary="Lil' Buddy cannot execute tasks that bypass Buddy Review.",
                risks=("review_required was false",),
                open_questions=("Should Buddy reissue the task with review_required=true?",),
            )
        if not task.approved_tools:
            return ResultEnvelope(
                task_id=task.task_id,
                worker=self.name,
                status="blocked",
                summary="No approved tool contracts were provided.",
                risks=("Worker execution requires an explicit tool contract, even for local demos.",),
            )

        tool_names = tuple(tool.name for tool in task.approved_tools)
        findings = (
            f"Preserved user intent: {task.user_intent}",
            f"Executed delegated scope only: {task.delegated_scope}",
            "Prepared local-only findings for Buddy Review.",
        )
        risks: tuple[str, ...] = ()
        if task.safety_class in ("high", "blocked"):
            risks = (
                f"Task safety class is {task.safety_class}; Buddy must review before any action.",
            )
        return ResultEnvelope(
            task_id=task.task_id,
            worker=self.name,
            status="complete",
            summary="Lil' Buddy completed the delegated local scope and returned structured results.",
            findings=findings,
            artifacts=("local-demo:buddy-lil-buddy-loop",),
            risks=risks,
            open_questions=(),
            tool_calls=tool_names,
        )
