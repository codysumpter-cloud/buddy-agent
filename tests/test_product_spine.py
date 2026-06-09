import json

from buddy_agent.cli_product_spine import run_product_spine_command
from buddy_agent.product_spine import (
    buddy_product_spine,
    product_spine_json,
    product_spine_summary_lines,
    validate_product_spine,
)


def test_product_spine_links_core_repos_and_surfaces():
    spine = buddy_product_spine()

    repos = {repo.name for repo in spine.repos}
    surfaces = {surface.id for surface in spine.surfaces}

    assert "codysumpter-cloud/prismtek-apps" in repos
    assert "codysumpter-cloud/buddy-agent" in repos
    assert "codysumpter-cloud/buddy-brain" in repos
    assert "agent-browser" in surfaces
    assert "bemore-workspace-runtime" in surfaces
    assert "buddy-playground" in surfaces
    assert "workspace-dispatch" in surfaces
    assert "browser-policy" in surfaces


def test_product_spine_flow_has_end_to_end_product_loop():
    spine = buddy_product_spine()

    flow_surfaces = [step.surface_id for step in spine.flow]

    assert flow_surfaces[0] == "agent-browser"
    assert "workspace-dispatch" in flow_surfaces
    assert "buddy-playground" in flow_surfaces
    assert "buddy-agent-runtime" in flow_surfaces
    assert "bemore-workspace-runtime" in flow_surfaces
    assert spine.flow[-1].risk == "external-action"


def test_product_spine_json_is_stable_and_valid():
    payload = json.loads(product_spine_json())

    assert payload["product"] == "Buddy / BeMore Agent Workspace"
    assert payload["version"] == "2026-06-09"
    assert len(payload["repos"]) == 3
    assert len(payload["flow"]) >= 6


def test_product_spine_validates_cleanly():
    assert validate_product_spine() == []


def test_product_spine_summary_reports_validation():
    lines = product_spine_summary_lines()

    assert any(line.startswith("product=Buddy / BeMore Agent Workspace") for line in lines)
    assert "validation=ok" in lines


def test_product_spine_cli_validate(capsys):
    exit_code = run_product_spine_command(["validate"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ok product-spine" in captured.out
