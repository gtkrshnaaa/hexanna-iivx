from pydantic import BaseModel, Field
from typing import Dict, Any
from hexanna.tools.base import BaseTool
from hexanna.ports.data_engine import IDataEngine

class SchemaInspectorInput(BaseModel):
    file_path: str = Field(description="Absolute or relative path to the local dataset (CSV/Parquet).")

class SchemaInspectorTool(BaseTool):
    name = "inspect_dataset_schema"
    description = (
        "Reads relational schema, data types, row counts, and disk footprint "
        "without loading raw records into memory or context window."
    )
    args_schema = SchemaInspectorInput

    def __init__(self, data_engine: IDataEngine):
        self.data_engine = data_engine

    def execute(self, file_path: str) -> Dict[str, Any]:
        metadata = self.data_engine.inspect_metadata(file_path)
        return {
            "file_path": metadata.file_path,
            "total_rows": metadata.row_count,
            "total_columns": metadata.column_count,
            "size_mb": round(metadata.size_in_bytes / (1024 * 1024), 2),
            "columns": [{"name": col.name, "type": col.data_type} for col in metadata.columns]
        }
