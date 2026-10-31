from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ILLMGateway(ABC):
    @abstractmethod
    def call_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Dispatches prompt with registered tools to an OpenAI-compatible remote endpoint."""
        pass
