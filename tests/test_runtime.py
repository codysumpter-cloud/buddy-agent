from buddy_agent.runtime import RuntimeConfig, RuntimeEngine, ToolDefinition, ToolResult


def test_runtime_records_messages_through_backend():
    engine = RuntimeEngine(session_id="session-1")

    response = engine.receive("hello")

    assert response.startswith("Buddy runtime [buddy-local] processed: hello")
    assert engine.state.session_id == "session-1"
    assert [message.role for message in engine.state.messages] == ["user", "assistant"]


def test_runtime_passes_context_to_backend():
    engine = RuntimeEngine(session_id="session-1")

    response = engine.receive("hello", context=("Local note: clean runtime seams",))

    assert "Context: Local note: clean runtime seams" in response


def test_runtime_accepts_explicit_config():
    engine = RuntimeEngine(
        session_id="session-1",
        config=RuntimeConfig(name="test-runtime", model="test-model"),
    )

    response = engine.receive("hello")

    assert "[test-model]" in response


def test_tool_registry_calls_registered_tool():
    engine = RuntimeEngine(session_id="session-1")

    def echo(arguments):
        return ToolResult(name="echo", ok=True, content=str(arguments["text"]))

    engine.tools.register(ToolDefinition(name="echo", description="Echo text.", handler=echo))

    result = engine.call_tool("echo", text="hi")

    assert result.ok is True
    assert result.content == "hi"
    assert engine.state.tool_results == [result]


def test_tool_registry_handles_unknown_tool():
    engine = RuntimeEngine(session_id="session-1")

    result = engine.call_tool("missing")

    assert result.ok is False
    assert "Unknown tool" in result.content
