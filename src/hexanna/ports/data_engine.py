from abc import ABC, abstractmethod
from typing import Dict, Any
from hexanna.domain.models import DatasetMetadata

class IDataEngine(ABC):
    @abstractmethod
    def inspect_metadata(self, file_path: str) -> DatasetMetadata:
        """Inspects structural metadata without reading payload into RAM."""
        pass

    @abstractmethod
    def execute_out_of_core_query(self, query: str, output_path: str) -> Dict[str, Any]:
        """Executes analytical SQL and writes directly to disk via out-of-core streaming."""
        pass

    @abstractmethod
    def compute_summary_sketches(self, file_path: str, column_name: str) -> Dict[str, Any]:
        """Calculates statistical sketches (nulls, quantiles, distincts) efficiently."""
        pass

    def execute_preview(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Executes analytical query with safe bounded row fetching for terminal preview."""
        raise NotImplementedError
