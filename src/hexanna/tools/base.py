from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from pydantic import BaseModel

class BaseTool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass

    def get_openai_schema(self) -> Dict[str, Any]:
        schema = self.args_schema.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", [])
                }
            }
        }
