import pytest
import os
import tempfile
import duckdb
from typing import List, Dict, Any
from hexanna.ports.llm_gateway import ILLMGateway
from hexanna.adapters.engine.duckdb_adapter import DuckDBAdapter

class MockLLMGateway(ILLMGateway):
    def __init__(self, responses: List[Dict[str, Any]] = None):
        self.responses = responses or []
        self.calls: List[Dict[str, Any]] = []

    def call_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        self.calls.append({"messages": messages, "tools_schema": tools_schema})
        if self.responses:
            return self.responses.pop(0)
        return {"role": "assistant", "content": "Done", "tool_calls": []}

@pytest.fixture
def mock_llm_gateway():
    return MockLLMGateway()

@pytest.fixture
def mock_llm_gateway_factory():
    def _create(responses=None):
        return MockLLMGateway(responses=responses)
    return _create

@pytest.fixture
def duckdb_engine():
    adapter = DuckDBAdapter(memory_limit="512MB")
    yield adapter
    adapter.close()

@pytest.fixture
def sample_parquet(tmp_path):
    file_path = str(tmp_path / "sample.parquet")
    conn = duckdb.connect()
    conn.execute(
        f"""
        COPY (
            SELECT 
                range as id,
                'user_' || (range % 10) as username,
                (range * 1.5) as score,
                CASE WHEN range % 5 = 0 THEN NULL ELSE 'active' END as status
            FROM range(1000)
        ) TO '{file_path}' (FORMAT PARQUET);
        """
    )
    conn.close()
    return file_path
