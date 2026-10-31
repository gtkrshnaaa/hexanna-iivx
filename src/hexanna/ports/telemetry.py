from abc import ABC, abstractmethod
from typing import Dict, Any

class ITelemetrySampler(ABC):
    @abstractmethod
    def sample(self) -> Dict[str, Any]:
        """Capture instantaneous resource consumption."""
        pass
