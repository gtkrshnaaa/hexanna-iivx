from dataclasses import dataclass

@dataclass(frozen=True)
class ResourcePolicy:
    """Enforces hardware safety boundaries for local execution."""
    max_memory: str = "2GB"
    max_memory_bytes: int = 2 * 1024 * 1024 * 1024
    temp_directory: str = ".hexanna_tmp"
    max_iterations: int = 10
    absolute_max_iterations: int = 20
    max_api_calls: int = 15
    max_consecutive_identical_calls: int = 3
    max_consecutive_errors: int = 4
    api_request_timeout: float = 60.0
    timeout_seconds: float = 300.0
    preserve_insertion_order: bool = False
