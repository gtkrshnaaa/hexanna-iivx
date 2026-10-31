import os
import json
import pytest
from typing import Optional, Dict, Any, Tuple
from hexanna.adapters.llm.openai_client import OpenAIGateway
from hexanna.tools.schema_inspector import SchemaInspectorTool
from hexanna.harness.runtime import HexannaRuntime

def _resolve_model_creds(model_type: str) -> Optional[Tuple[str, str, str]]:
    """Loads air-gapped credentials securely from local models.json or environment."""
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "..", "benchmarks", "local", "models.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if model_type in data:
                    item = data[model_type]
                    base_url = item.get("base_url")
                    api_key = item.get("api_key")
                    model_id = item.get("model_id")
                    if base_url and api_key and model_id and not api_key.startswith("your_"):
                        return base_url, api_key, model_id
        except Exception:
            pass

    prefix = model_type.upper()
    url = os.getenv(f"{prefix}_BASE_URL")
    key = os.getenv(f"{prefix}_API_KEY")
    mid = os.getenv(f"{prefix}_MODEL")
    if url and key and mid and not key.startswith("your_"):
        return url, key, mid

    return None

def test_deepseek_live_chat_completion():
    creds = _resolve_model_creds("deepseek")
    if not creds:
        pytest.skip("Air-gapped DeepSeek credentials not available.")

    base_url, api_key, model_id = creds
    gateway = OpenAIGateway(base_url=base_url, api_key=api_key, model_name=model_id)

    resp = gateway.call_with_tools(
        messages=[{"role": "user", "content": "Respond strictly with the single word: READY"}],
        tools_schema=[]
    )

    assert resp["role"] == "assistant"
    assert isinstance(resp["content"], str)
    assert resp["usage"]["total_tokens"] > 0

def test_gemini_live_chat_completion():
    creds = _resolve_model_creds("gemini")
    if not creds:
        pytest.skip("Air-gapped Gemini credentials not available.")

    base_url, api_key, model_id = creds
    gateway = OpenAIGateway(base_url=base_url, api_key=api_key, model_name=model_id)

    resp = gateway.call_with_tools(
        messages=[{"role": "user", "content": "Respond strictly with the single word: READY"}],
        tools_schema=[]
    )

    assert resp["role"] == "assistant"
    assert len(resp["content"]) > 0
    assert resp["usage"]["total_tokens"] > 0

def test_deepseek_live_tool_calling():
    creds = _resolve_model_creds("deepseek")
    if not creds:
        pytest.skip("Air-gapped DeepSeek credentials not available.")

    base_url, api_key, model_id = creds
    gateway = OpenAIGateway(base_url=base_url, api_key=api_key, model_name=model_id)

    tool_schema = [{
        "type": "function",
        "function": {
            "name": "inspect_dataset_schema",
            "description": "Inspects dataset column names and data types from a parquet file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to parquet file"}
                },
                "required": ["file_path"]
            }
        }
    }]

    resp = gateway.call_with_tools(
        messages=[{"role": "user", "content": "Inspect the dataset schema for /tmp/sales.parquet using the function."}],
        tools_schema=tool_schema
    )

    assert resp["role"] == "assistant"
    assert len(resp["tool_calls"]) > 0
    tc = resp["tool_calls"][0]
    assert tc["name"] == "inspect_dataset_schema"
    assert "file_path" in tc["arguments"]

def test_live_hexanna_runtime_with_deepseek(sample_parquet, duckdb_engine):
    creds = _resolve_model_creds("deepseek")
    if not creds:
        pytest.skip("Air-gapped DeepSeek credentials not available.")

    base_url, api_key, model_id = creds
    gateway = OpenAIGateway(base_url=base_url, api_key=api_key, model_name=model_id)
    tools = [SchemaInspectorTool(duckdb_engine)]
    runtime = HexannaRuntime(llm_gateway=gateway, tools=tools)

    state = runtime.run(
        f"Inspect dataset schema for '{sample_parquet}' and summarize its fields.",
        max_iterations=3
    )

    assert state.completed is True
    assert state.iteration >= 1
    assert any(h["tool"] == "inspect_dataset_schema" for h in state.history)
