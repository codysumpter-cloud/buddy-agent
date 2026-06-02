"""Buddy-native Symphony workflow and local work-runner contracts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_WORKFLOW_SECTIONS = ("tracker", "workspace", "hooks", "agent", "codex")
SAFE_SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass(frozen=True)
class BuddyWorkIssue:
    """A local issue shape compatible with Symphony-style tracked work."""

    identifier: str
    title: str
    body: str = ""
    priority: str = "normal"

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> BuddyWorkIssue:
        """Build an issue from a JSON object."""
        identifier = str(value.get("identifier") or value.get("id") or "LOCAL-1")
        title = str(value.get("title") or "Local Buddy work item")
        body = str(value.get("body") or value.get("description") or "")
        priority = str(value.get("priority") or "normal")
        return cls(identifier=identifier, title=title, body=body, priority=priority)

    def template_values(self) -> dict[str, str]:
        """Return values usable for lightweight template expansion."""
        return {
            "issue.identifier": self.identifier,
            "issue.title": self.title,
            "issue.body": self.body,
            "issue.priority": self.priority,
        }


@dataclass(frozen=True)
class BuddyWorkflow:
    """Parsed Buddy/Symphony workflow."""

    path: Path | None
    front_matter: dict[str, dict[str, str]]
    body: str

    def validate(self) -> tuple[str, ...]:
        """Return workflow problems. Empty means the workflow is usable."""
        problems: list[str] = []
        for section in REQUIRED_WORKFLOW_SECTIONS:
            if section not in self.front_matter:
                problems.append(f"missing section: {section}")
        if not self.body.strip():
            problems.append("workflow body must not be empty")
        return tuple(problems)

    def section(self, name: str) -> dict[str, str]:
        """Return a front-matter section."""
        return self.front_matter.get(name, {})

    def workspace_root(self) -> Path:
        """Return the configured workspace root."""
        raw = self.section("workspace").get("root") or ".buddy/workspaces"
        return Path(raw).expanduser()

    def tracker_path(self) -> Path | None:
        """Return an optional local tracker path."""
        raw = self.section("tracker").get("path")
        return Path(raw).expanduser() if raw else None

    def render_prompt(self, issue: BuddyWorkIssue) -> str:
        """Render the workflow body with issue placeholders."""
        rendered = self.body
        for key, value in issue.template_values().items():
            rendered = rendered.replace("{{ " + key + " }}", value)
            rendered = rendered.replace("{{" + key + "}}", value)
        return rendered.strip()


@dataclass(frozen=True)
class BuddyWorkRunPlan:
    """A local, explicit-run work plan generated from a workflow."""

    workflow_path: Path | None
    issue: BuddyWorkIssue
    workspace_path: Path
    prompt: str
    codex_command: str
    hook_names: tuple[str, ...] = field(default_factory=tuple)
    created_files: tuple[Path, ...] = field(default_factory=tuple)

    def summary_lines(self) -> tuple[str, ...]:
        """Return CLI-friendly plan output."""
        return (
            f"issue={self.issue.identifier}",
            f"title={self.issue.title}",
            f"workspace={self.workspace_path}",
            f"codex_command={self.codex_command}",
            "hooks=" + (",".join(self.hook_names) if self.hook_names else "none"),
            "created_files=" + ",".join(str(path) for path in self.created_files),
            "mode=local_plan_no_external_services_started",
        )


def safe_slug(value: str) -> str:
    """Return a filesystem-safe slug."""
    cleaned = SAFE_SLUG_RE.sub("-", value.strip()).strip(".-_")
    return cleaned[:80] or "buddy-work"


def parse_workflow_text(text: str, *, path: Path | None = None) -> BuddyWorkflow:
    """Parse a minimal Symphony-style Markdown workflow file."""
    front_matter_text = ""
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            front_matter_text = parts[1]
            body = parts[2]
    return BuddyWorkflow(
        path=path,
        front_matter=parse_front_matter(front_matter_text),
        body=body.strip(),
    )


def load_workflow(path: str | Path) -> BuddyWorkflow:
    """Load a workflow from disk."""
    workflow_path = Path(path).expanduser()
    text = workflow_path.read_text(encoding="utf-8")
    return parse_workflow_text(text, path=workflow_path)


def parse_front_matter(text: str) -> dict[str, dict[str, str]]:
    """Parse the limited YAML shape Buddy needs without adding dependencies."""
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith((" ", "\t")) and raw_line.rstrip().endswith(":"):
            current = raw_line.strip()[:-1]
            sections[current] = {}
            continue
        if current is None or ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        sections[current][key.strip()] = value.strip().strip('"\'')
    return sections


def load_local_issue(path: Path | None) -> BuddyWorkIssue:
    """Load the first pending local issue from JSON, or return a smoke issue."""
    if path is None or not path.exists():
        return BuddyWorkIssue(
            identifier="LOCAL-1",
            title="Buddy local Symphony smoke work",
            body="Verify the Buddy Symphony work-runner path.",
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list) and raw:
        first = raw[0]
        if isinstance(first, dict):
            return BuddyWorkIssue.from_json(first)
    if isinstance(raw, dict):
        issues = raw.get("issues")
        if isinstance(issues, list) and issues and isinstance(issues[0], dict):
            return BuddyWorkIssue.from_json(issues[0])
        return BuddyWorkIssue.from_json(raw)
    raise ValueError(f"Unsupported local tracker shape: {path}")


def build_work_run_plan(workflow: BuddyWorkflow) -> BuddyWorkRunPlan:
    """Build a local work-run plan from a parsed workflow."""
    problems = workflow.validate()
    if problems:
        raise ValueError("Invalid workflow: " + "; ".join(problems))
    issue = load_local_issue(workflow.tracker_path())
    root = workflow.workspace_root()
    workspace_name = safe_slug(issue.identifier + "-" + issue.title)
    workspace_path = root / workspace_name
    codex_command = workflow.section("codex").get("command") or "codex app-server"
    hooks = tuple(sorted(workflow.section("hooks").keys()))
    return BuddyWorkRunPlan(
        workflow_path=workflow.path,
        issue=issue,
        workspace_path=workspace_path,
        prompt=workflow.render_prompt(issue),
        codex_command=codex_command,
        hook_names=hooks,
    )


def create_local_workspace(plan: BuddyWorkRunPlan) -> BuddyWorkRunPlan:
    """Create the local workspace files for a work-run plan.

    This intentionally does not execute hooks or launch external worker processes.
    """
    plan.workspace_path.mkdir(parents=True, exist_ok=True)
    prompt_path = plan.workspace_path / "BUDDY_WORK_PROMPT.md"
    receipt_path = plan.workspace_path / "buddy_work_run.json"
    prompt_path.write_text(plan.prompt + "\n", encoding="utf-8")
    receipt = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "issue": {
            "identifier": plan.issue.identifier,
            "title": plan.issue.title,
            "priority": plan.issue.priority,
        },
        "workflow_path": str(plan.workflow_path) if plan.workflow_path else None,
        "workspace_path": str(plan.workspace_path),
        "codex_command": plan.codex_command,
        "hooks_detected": list(plan.hook_names),
        "external_services_started": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return BuddyWorkRunPlan(
        workflow_path=plan.workflow_path,
        issue=plan.issue,
        workspace_path=plan.workspace_path,
        prompt=plan.prompt,
        codex_command=plan.codex_command,
        hook_names=plan.hook_names,
        created_files=(prompt_path, receipt_path),
    )


def workflow_contract_lines(path: str | Path | None = None) -> tuple[str, ...]:
    """Return workflow contract validation output."""
    if path is None:
        return (
            "workflow contract ready",
            "required_sections=" + ",".join(REQUIRED_WORKFLOW_SECTIONS),
            "services_started=false",
        )
    workflow = load_workflow(path)
    problems = workflow.validate()
    if problems:
        return ("workflow contract invalid", "problems=" + "; ".join(problems))
    return (
        "workflow contract valid",
        "sections=" + ",".join(sorted(workflow.front_matter)),
        f"body_chars={len(workflow.body)}",
    )


def workspace_plan_lines(path: str | Path) -> tuple[str, ...]:
    """Return a workspace plan without creating files."""
    plan = build_work_run_plan(load_workflow(path))
    return plan.summary_lines()


def work_runner_lines(path: str | Path) -> tuple[str, ...]:
    """Create a local workspace and return the run plan summary."""
    plan = build_work_run_plan(load_workflow(path))
    created = create_local_workspace(plan)
    return created.summary_lines()


def local_tracker_lines(path: str | Path | None = None) -> tuple[str, ...]:
    """Return local tracker status lines."""
    issue = load_local_issue(Path(path).expanduser() if path else None)
    return (
        "tracker=local-json",
        f"next_issue={issue.identifier}",
        f"title={issue.title}",
        f"priority={issue.priority}",
    )


def worker_bridge_lines() -> tuple[str, ...]:
    """Return a safe worker bridge status without launching a process."""
    return (
        "worker_bridge=codex-app-server-compatible",
        "launch_mode=explicit_external_only",
        "default_action=plan_only_no_process_started",
    )


def observability_lines() -> tuple[str, ...]:
    """Return local observability surface information."""
    return (
        "observability=local-json-receipt",
        "dashboard=not_started_by_default",
        "api=contract_only",
    )
