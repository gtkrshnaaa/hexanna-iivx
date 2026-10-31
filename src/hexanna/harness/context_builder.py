import json
from typing import Dict, Any

class MetadataContextBuilder:
    @staticmethod
    def build_system_prompt() -> str:
        return (
            "You are Hexanna IIVX, an autonomous, deterministic Data Engineering Agent "
            "running locally on a commodity developer workstation.\n"
            "OPERATING CONSTRAINTS:\n"
            "1. NEVER request raw records, shell commands, or full data dumping.\n"
            "2. All transformations MUST operate through provided out-of-core tools.\n"
            "3. Formulate SQL queries that project only necessary columns and persist directly to disk.\n"
            "4. Your goal is to deliver reproducible data pipelines without memory spikes."
        )

    @staticmethod
    def format_tool_response(tool_call_id: str, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result)
        }
