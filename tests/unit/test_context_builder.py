from hexanna.harness.context_builder import MetadataContextBuilder

def test_system_prompt_constraints():
    prompt = MetadataContextBuilder.build_system_prompt()
    assert "Hexanna IIVX" in prompt
    assert "NEVER request raw records" in prompt
    assert "out-of-core" in prompt

def test_format_tool_response():
    resp = MetadataContextBuilder.format_tool_response(
        tool_call_id="call_123",
        tool_name="inspect_dataset_schema",
        result={"rows": 1000, "columns": 4}
    )
    assert resp["role"] == "tool"
    assert resp["tool_call_id"] == "call_123"
    assert resp["name"] == "inspect_dataset_schema"
    assert '"rows": 1000' in resp["content"]
