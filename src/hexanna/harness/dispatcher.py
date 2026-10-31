from typing import List, Dict, Any
from hexanna.tools.base import BaseTool

class ToolDispatcher:
    """Validates arguments against tool schemas and dispatches execution safely."""

    def __init__(self, tools: List[BaseTool]):
        self._tools_map = {tool.name: tool for tool in tools}

    @property
    def tools(self) -> List[BaseTool]:
        return list(self._tools_map.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.get_openai_schema() for tool in self._tools_map.values()]

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools_map

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self._tools_map:
            return {"error": f"Tool '{tool_name}' is unauthorized or does not exist."}
        try:
            tool = self._tools_map[tool_name]
            return tool.execute(**arguments)
        except Exception as err:
            return {"error": str(err)}
