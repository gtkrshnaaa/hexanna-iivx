import os
import psutil
from typing import Dict, Any
from hexanna.ports.telemetry import ITelemetrySampler

class PsutilTracker(ITelemetrySampler):
    """Tracks local process memory and CPU consumption without invasive overhead."""

    def __init__(self, pid: int = os.getpid()):
        self.process = psutil.Process(pid)

    def sample(self) -> Dict[str, Any]:
        try:
            mem_info = self.process.memory_info()
            cpu_pct = self.process.cpu_percent(interval=None)
            return {
                "rss_mb": round(mem_info.rss / (1024 * 1024), 2),
                "vms_mb": round(mem_info.vms / (1024 * 1024), 2),
                "cpu_percent": cpu_pct
            }
        except psutil.NoSuchProcess:
            return {
                "rss_mb": 0.0,
                "vms_mb": 0.0,
                "cpu_percent": 0.0
            }
