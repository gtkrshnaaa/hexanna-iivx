import os
from hexanna.harness.runtime import HexannaRuntime
from hexanna.tools.schema_inspector import SchemaInspectorTool
from hexanna.tools.out_of_core_sql import OutOfCoreSQLTool
from tests.conftest import MockLLMGateway

def test_full_pipeline_execution(sample_parquet, duckdb_engine, tmp_path):
    output_target = str(tmp_path / "final_summary.parquet")
    tools = [
        SchemaInspectorTool(duckdb_engine),
        OutOfCoreSQLTool(duckdb_engine)
    ]

    mock_responses = [
        # Step 1: LLM inspects schema
        {
            "role": "assistant",
            "content": "Let me inspect the schema first.",
            "tool_calls": [
                {
                    "id": "call_1",
                    "name": "inspect_dataset_schema",
                    "arguments": {"file_path": sample_parquet}
                }
            ]
        },
        # Step 2: LLM executes out-of-core transformation
        {
            "role": "assistant",
            "content": "Now transforming out-of-core.",
            "tool_calls": [
                {
                    "id": "call_2",
                    "name": "execute_out_of_core_sql",
                    "arguments": {
                        "query": f"SELECT username, count(*) as cnt FROM '{sample_parquet}' GROUP BY username",
                        "output_path": output_target
                    }
                }
            ]
        },
        # Step 3: LLM finishes task
        {
            "role": "assistant",
            "content": "Pipeline completed successfully with all aggregates written to disk.",
            "tool_calls": []
        }
    ]

    gateway = MockLLMGateway(responses=mock_responses)
    runtime = HexannaRuntime(llm_gateway=gateway, tools=tools)

    state = runtime.run("Aggregate usernames and write to parquet.", max_iterations=5)

    assert state.completed is True
    assert state.iteration == 3
    assert output_target in state.artifacts_created
    assert os.path.exists(output_target)
