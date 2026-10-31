from pydantic import BaseModel, Field
from typing import Dict, Any
from hexanna.tools.base import BaseTool
from hexanna.ports.data_engine import IDataEngine

class OutOfCoreSQLInput(BaseModel):
    query: str = Field(description="DuckDB SQL expression. Query dataset directly via file path syntax: 'data/file.parquet'.")
    output_path: str = Field(description="Destination file path where transformed records are persisted (Parquet format).")

class OutOfCoreSQLTool(BaseTool):
    name = "execute_out_of_core_sql"
    description = (
        "Executes memory-bounded SQL transformations on disk-based datasets and writes output "
        "directly to a Parquet file. Guaranteed out-of-core and zero RAM exhaustion."
    )
    args_schema = OutOfCoreSQLInput

    def __init__(self, data_engine: IDataEngine):
        self.data_engine = data_engine

    def execute(self, query: str, output_path: str) -> Dict[str, Any]:
        return self.data_engine.execute_out_of_core_query(query, output_path)
