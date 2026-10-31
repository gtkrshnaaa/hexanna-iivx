from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True)
class ColumnSchema:
    name: str
    data_type: str
    nullable: bool = True

@dataclass(frozen=True)
class DatasetMetadata:
    file_path: str
    row_count: int
    column_count: int
    columns: List[ColumnSchema]
    size_in_bytes: int
    file_format: str

@dataclass
class ToolExecutionResult:
    tool_name: str
    success: bool
    output: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0

@dataclass
class ExecutionState:
    task_id: str
    objective: str
    iteration: int = 0
    max_iterations: int = 10
    history: List[Dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    artifacts_created: List[str] = field(default_factory=list)
