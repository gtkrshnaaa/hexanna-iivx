import time
import psutil
import threading
from typing import List, Dict

class MemoryDaemon:
    def __init__(self, target_pid: int, sampling_interval_sec: float = 0.05):
        self.process = psutil.Process(target_pid)
        self.interval = sampling_interval_sec
        self.samples: List[Dict[str, float]] = []
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._monitor)

    def start(self):
        self._stop_event.clear()
        self._thread.start()

    def stop(self) -> List[Dict[str, float]]:
        self._stop_event.set()
        self._thread.join()
        return self.samples

    def _monitor(self):
        start_time = time.time()
        while not self._stop_event.is_set():
            try:
                mem_info = self.process.memory_info()
                cpu_pct = self.process.cpu_percent(interval=None)
                elapsed = time.time() - start_time
                self.samples.append({
                    "timestamp": elapsed,
                    "rss_mb": mem_info.rss / (1024 * 1024),
                    "vms_mb": mem_info.vms / (1024 * 1024),
                    "cpu_percent": cpu_pct
                })
            except psutil.NoSuchProcess:
                break
            time.sleep(self.interval)

    def get_peak_rss(self) -> float:
        if not self.samples:
            return 0.0
        return max(s["rss_mb"] for s in self.samples)
