import json

from buddy_agent.agent_readiness.economics import TaskEconomics, TaskEconomicsWriter


def test_verified_completion_requires_all_gates():
    record = TaskEconomics("task", "openai", "gpt-test", 1, 1, 0, 100, 1, True, True, security_gate="pass")
    blocked = TaskEconomics("task2", "openai", "gpt-test", 1, 1, 0, 100, 1, True, True, security_gate="block")
    assert record.verified_completion
    assert not blocked.verified_completion


def test_writer_emits_prompt_free_jsonl(tmp_path):
    path = tmp_path / "economics.jsonl"
    record = TaskEconomics("task", "openai", "gpt-test", 2, 1.25, 0.5, 1000, 4, True, True)
    TaskEconomicsWriter(path).write(record)
    payload = json.loads(path.read_text())
    assert payload["attempts"] == 2
    assert "prompt" not in payload
