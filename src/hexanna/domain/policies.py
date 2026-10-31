from dataclasses import dataclass

@dataclass(frozen=True)
class ResourcePolicy:
    """Enforces hardware safety boundaries for local execution."""
    max_memory: str = "2GB"
    max_memory_bytes: int = 2 * 1024 * 1024 * 1024
    temp_directory: str = ".hexanna_tmp"
    max_iterations: int = 10
    timeout_seconds: float = 300.0
    preserve_insertion_order: bool = False
