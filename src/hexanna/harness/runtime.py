import time
import json
from typing import List, Dict, Any, Optional
from hexanna.ports.llm_gateway import ILLMGateway
from hexanna.ports.chat_history import IChatHistoryRepository
from hexanna.tools.base import BaseTool
from hexanna.harness.context_builder import MetadataContextBuilder
from hexanna.harness.dispatcher import ToolDispatcher
from hexanna.domain.models import ExecutionState

class HexannaRuntime:
    def __init__(
        self,
        llm_gateway: ILLMGateway,
        tools: List[BaseTool],
        history_repo: Optional[IChatHistoryRepository] = None
    ):
        self.llm_gateway = llm_gateway
        self.dispatcher = ToolDispatcher(tools)
        self.history_repo = history_repo

    def run(
        self,
        objective: str,
        max_iterations: int = 10,
        session_id: Optional[str] = None
    ) -> ExecutionState:
        sid = session_id or f"hexanna-{int(time.time())}"
        state = ExecutionState(
            task_id=sid,
            objective=objective,
            max_iterations=max_iterations
        )

        if self.history_repo:
            self.history_repo.create_session(session_id=sid, title=objective[:60])
            self.history_repo.add_message(session_id=sid, role="user", content=objective)

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
            if self.history_repo:
                self.history_repo.add_message(
                    session_id=sid,
                    role="assistant",
                    content=content
                )

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
                if self.history_repo:
                    self.history_repo.add_message(
                        session_id=sid,
                        role="tool",
                        content=json.dumps(exec_result),
                        tool_call_id=call_id,
                        tool_name=fn_name,
                        tool_arguments=args,
                        tool_result=exec_result
                    )
                state.history.append({
                    "iteration": state.iteration,
                    "tool": fn_name,
                    "args": args,
                    "output": exec_result
                })

        return state
