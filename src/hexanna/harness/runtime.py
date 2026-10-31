import time
import json
from typing import List, Dict, Any
from hexanna.ports.llm_gateway import ILLMGateway
from hexanna.tools.base import BaseTool
from hexanna.harness.context_builder import MetadataContextBuilder
from hexanna.harness.dispatcher import ToolDispatcher
from hexanna.domain.models import ExecutionState

class HexannaRuntime:
    def __init__(self, llm_gateway: ILLMGateway, tools: List[BaseTool]):
        self.llm_gateway = llm_gateway
        self.dispatcher = ToolDispatcher(tools)

    def run(self, objective: str, max_iterations: int = 10) -> ExecutionState:
        state = ExecutionState(
            task_id=f"hexanna-{int(time.time())}",
            objective=objective,
            max_iterations=max_iterations
        )

        messages = [
            {"role": "system", "content": MetadataContextBuilder.build_system_prompt()},
            {"role": "user", "content": objective}
        ]

        while state.iteration < max_iterations and not state.completed:
            state.iteration += 1
            response = self.llm_gateway.call_with_tools(messages, self.dispatcher.get_schemas())

            tool_calls = response.get("tool_calls", [])
            content = response.get("content")

            assistant_msg: Dict[str, Any] = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": (
                                json.dumps(tc["arguments"])
                                if isinstance(tc["arguments"], dict)
                                else str(tc["arguments"])
                            )
                        }
                    }
                    for tc in tool_calls
                ]
            messages.append(assistant_msg)

            if not tool_calls:
                state.completed = True
                break

            for tc in tool_calls:
                fn_name = tc["name"]
                args = tc["arguments"]
                call_id = tc["id"]

                exec_result = self.dispatcher.dispatch(fn_name, args)
                if isinstance(exec_result, dict) and "destination" in exec_result:
                    state.artifacts_created.append(exec_result["destination"])

                tool_msg = MetadataContextBuilder.format_tool_response(call_id, fn_name, exec_result)
                messages.append(tool_msg)
                state.history.append({
                    "iteration": state.iteration,
                    "tool": fn_name,
                    "args": args,
                    "output": exec_result
                })

        return state
