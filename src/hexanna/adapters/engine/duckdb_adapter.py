import os
import duckdb
from typing import Dict, Any, List
from hexanna.ports.data_engine import IDataEngine
from hexanna.domain.models import DatasetMetadata, ColumnSchema
from hexanna.domain.exceptions import HexannaDomainException

class DuckDBAdapter(IDataEngine):
    def __init__(self, memory_limit: str = "2GB", temp_directory: str = ".hexanna_tmp"):
        self.memory_limit = memory_limit
        self.temp_directory = temp_directory
        os.makedirs(self.temp_directory, exist_ok=True)

        self._conn = duckdb.connect(database=":memory:")
        self._conn.execute(f"SET max_memory = '{self.memory_limit}';")
        self._conn.execute(f"SET temp_directory = '{self.temp_directory}';")
        self._conn.execute("SET preserve_insertion_order = false;")

    def inspect_metadata(self, file_path: str) -> DatasetMetadata:
        if not os.path.exists(file_path):
            raise HexannaDomainException(f"Dataset path not found: {file_path}")

        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        describe_query = f"DESCRIBE SELECT * FROM '{file_path}'"
        desc_records = self._conn.execute(describe_query).fetchall()

        count_query = f"SELECT COUNT(*) FROM '{file_path}'"
        total_rows = self._conn.execute(count_query).fetchone()[0]

        columns = [
            ColumnSchema(name=row[0], data_type=row[1], nullable=(row[2] == "YES"))
            for row in desc_records
        ]

        return DatasetMetadata(
            file_path=file_path,
            row_count=total_rows,
            column_count=len(columns),
            columns=columns,
            size_in_bytes=file_size,
            file_format=ext.replace(".", "")
        )

    def execute_out_of_core_query(self, query: str, output_path: str) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        wrapped_query = f"COPY ({query}) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD);"

        self._conn.execute(wrapped_query)
        output_size = os.path.getsize(output_path)
        row_count = self._conn.execute(f"SELECT COUNT(*) FROM '{output_path}'").fetchone()[0]

        return {
            "status": "success",
            "destination": output_path,
            "rows_written": row_count,
            "output_size_bytes": output_size
        }

    def compute_summary_sketches(self, file_path: str, column_name: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise HexannaDomainException(f"Dataset path not found: {file_path}")

        sql = f"""
            SELECT 
                COUNT({column_name}) as non_null_count,
                COUNT(*) - COUNT({column_name}) as null_count,
                COUNT(DISTINCT {column_name}) as approx_distinct,
                MIN({column_name}) as min_val,
                MAX({column_name}) as max_val
            FROM '{file_path}'
        """
        cursor = self._conn.execute(sql)
        row = cursor.fetchone()
        col_names = [desc[0] for desc in cursor.description]
        return dict(zip(col_names, row))

    def execute_preview(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Executes analytical query with safe bounded row fetching for terminal preview."""
        clean_query = query.strip().rstrip(";")
        preview_sql = f"SELECT * FROM ({clean_query}) LIMIT {limit}"
        cursor = self._conn.execute(preview_sql)
        headers = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return {
            "columns": headers,
            "rows": rows,
            "row_count": len(rows),
            "is_truncated": len(rows) == limit
        }

    def close(self):
        if self._conn:
            self._conn.close()
