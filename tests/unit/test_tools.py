import os
from hexanna.tools.schema_inspector import SchemaInspectorTool
from hexanna.tools.out_of_core_sql import OutOfCoreSQLTool
from hexanna.tools.profile_sketcher import ProfileSketcherTool

def test_schema_inspector_tool(sample_parquet, duckdb_engine):
    tool = SchemaInspectorTool(duckdb_engine)
    res = tool.execute(file_path=sample_parquet)
    assert res["total_rows"] == 1000
    assert res["total_columns"] == 4
    assert len(res["columns"]) == 4

def test_out_of_core_sql_tool(sample_parquet, duckdb_engine, tmp_path):
    tool = OutOfCoreSQLTool(duckdb_engine)
    out_path = str(tmp_path / "filtered.parquet")
    res = tool.execute(
        query=f"SELECT * FROM '{sample_parquet}' WHERE id < 100",
        output_path=out_path
    )
    assert res["status"] == "success"
    assert res["rows_written"] == 100
    assert os.path.exists(out_path)

def test_profile_sketcher_tool(sample_parquet, duckdb_engine):
    tool = ProfileSketcherTool(duckdb_engine)
    res = tool.execute(file_path=sample_parquet, column_name="score")
    assert res["non_null_count"] == 1000
    assert res["min_val"] == 0.0
    assert res["max_val"] == 1498.5

def test_tool_openai_schema(duckdb_engine):
    tool = SchemaInspectorTool(duckdb_engine)
    schema = tool.get_openai_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "inspect_dataset_schema"
    assert "file_path" in schema["function"]["parameters"]["properties"]
