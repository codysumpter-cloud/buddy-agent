from buddy_agent.adapters import AdapterHealth


def test_adapter_health_shape():
    health = AdapterHealth(name="vault", ok=True, detail="ready")

    assert health.name == "vault"
    assert health.ok is True
    assert health.detail == "ready"
