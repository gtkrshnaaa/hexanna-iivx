from pydantic import BaseModel, Field
from typing import Dict, Any
from hexanna.tools.base import BaseTool
from hexanna.ports.data_engine import IDataEngine

class ProfileSketcherInput(BaseModel):
    file_path: str = Field(description="Target dataset path.")
    column_name: str = Field(description="Specific column name to profile.")

class ProfileSketcherTool(BaseTool):
    name = "profile_column_sketches"
    description = "Computes null rates, cardinalities, and boundary values for a column without full dataset scanning."
    args_schema = ProfileSketcherInput

    def __init__(self, data_engine: IDataEngine):
        self.data_engine = data_engine

    def execute(self, file_path: str, column_name: str) -> Dict[str, Any]:
        return self.data_engine.compute_summary_sketches(file_path, column_name)
