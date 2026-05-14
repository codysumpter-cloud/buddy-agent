import json

import pytest

from buddy_agent.runtime import RuntimeConfig, load_runtime_config


def test_runtime_config_defaults_are_safe():
    config = RuntimeConfig()

    assert config.backend == "local-template"
    assert config.name == "buddy-alpha-plus"
    assert config.restricted_integrations_enabled is False


def test_runtime_config_loads_json_file(tmp_path):
    path = tmp_path / "buddy-runtime.json"
    path.write_text(json.dumps({"name": "test-plus", "memory_limit": 2}), encoding="utf-8")

    config = load_runtime_config(path)

    assert config.name == "test-plus"
    assert config.memory_limit == 2


def test_runtime_config_rejects_non_object_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_runtime_config(path)
