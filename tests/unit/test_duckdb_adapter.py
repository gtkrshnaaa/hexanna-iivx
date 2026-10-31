import os
import pytest
from hexanna.adapters.engine.duckdb_adapter import DuckDBAdapter
from hexanna.domain.exceptions import HexannaDomainException

def test_inspect_metadata(sample_parquet, duckdb_engine):
    metadata = duckdb_engine.inspect_metadata(sample_parquet)
    assert metadata.row_count == 1000
    assert metadata.column_count == 4
    col_names = [col.name for col in metadata.columns]
    assert "id" in col_names
    assert "username" in col_names
    assert "score" in col_names
    assert "status" in col_names

def test_inspect_missing_file_raises(duckdb_engine):
    with pytest.raises(HexannaDomainException):
        duckdb_engine.inspect_metadata("non_existent_file.parquet")

def test_execute_out_of_core_query(sample_parquet, duckdb_engine, tmp_path):
    out_file = str(tmp_path / "aggregated.parquet")
    query = f"SELECT username, SUM(score) as total_score FROM '{sample_parquet}' GROUP BY username"
    result = duckdb_engine.execute_out_of_core_query(query, out_file)

    assert result["status"] == "success"
    assert result["destination"] == out_file
    assert result["rows_written"] == 10
    assert os.path.exists(out_file)

def test_compute_summary_sketches(sample_parquet, duckdb_engine):
    sketch = duckdb_engine.compute_summary_sketches(sample_parquet, "status")
    assert sketch["null_count"] == 200
    assert sketch["non_null_count"] == 800
    assert sketch["approx_distinct"] == 1

def test_duckdb_threads_configuration():
    adapter = DuckDBAdapter(memory_limit="1GB", threads=2)
    assert adapter.threads == 2
    res = adapter._conn.execute("SELECT current_setting('threads')").fetchone()[0]
    assert int(res) == 2
    adapter.close()
