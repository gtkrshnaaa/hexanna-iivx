import time
import json
from typing import List, Dict, Any, Optional
from hexanna.ports.llm_gateway import ILLMGateway
from hexanna.ports.chat_history import IChatHistoryRepository
from hexanna.tools.base import BaseTool
from hexanna.harness.context_builder import MetadataContextBuilder
from hexanna.harness.dispatcher import ToolDispatcher
from hexanna.domain.models import ExecutionState
from hexanna.domain.policies import ResourcePolicy
from hexanna.domain.exceptions import InfiniteLoopDetectedException

class HexannaRuntime:
    def __init__(
        self,
        llm_gateway: ILLMGateway,
        tools: List[BaseTool],
        history_repo: Optional[IChatHistoryRepository] = None,
        policy: Optional[ResourcePolicy] = None
    ):
        self.llm_gateway = llm_gateway
        self.dispatcher = ToolDispatcher(tools)
        self.history_repo = history_repo
        self.policy = policy or ResourcePolicy()

    def run(
        self,
        objective: str,
        max_iterations: int = 10,
        session_id: Optional[str] = None
    ) -> ExecutionState:
        sid = session_id or f"hexanna-{int(time.time())}"
        bounded_iterations = max(1, min(max_iterations, self.policy.absolute_max_iterations))
        state = ExecutionState(
            task_id=sid,
            objective=objective,
            max_iterations=bounded_iterations
        )

        if self.history_repo:
            self.history_repo.create_session(session_id=sid, title=objective[:60])
            self.history_repo.add_message(session_id=sid, role="user", content=objective)

        messages = [
            {"role": "system", "content": MetadataContextBuilder.build_system_prompt()},
            {"role": "user", "content": objective}
        ]

        last_call_signature = None
        consecutive_identical_calls = 0
        consecutive_tool_errors = 0

        while state.iteration < bounded_iterations and not state.completed:
            if state.api_calls >= self.policy.max_api_calls:
                raise InfiniteLoopDetectedException(
                    f"Circuit breaker triggered: exceeded maximum allowed API calls ({self.policy.max_api_calls})."
                )

            state.iteration += 1
            state.api_calls += 1
            response = self.llm_gateway.call_with_tools(messages, self.dispatcher.get_schemas())

            if not response or not isinstance(response, dict):
                state.completed = True
                break

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

            # Cyclic tool call loop detection
            current_signature = tuple(
                (tc.get("name"), json.dumps(tc.get("arguments", {}), sort_keys=True))
                for tc in tool_calls
            )
            if current_signature and current_signature == last_call_signature:
                consecutive_identical_calls += 1
                if consecutive_identical_calls >= self.policy.max_consecutive_identical_calls:
                    raise InfiniteLoopDetectedException(
                        f"Circuit breaker triggered: detected cyclic loop with identical tool calls ({current_signature[0][0]}) repeated {consecutive_identical_calls + 1} times."
                    )
            else:
                consecutive_identical_calls = 0
            last_call_signature = current_signature

            for tc in tool_calls:
                fn_name = tc["name"]
                args = tc["arguments"]
                call_id = tc["id"]

                exec_result = self.dispatcher.dispatch(fn_name, args)
                if isinstance(exec_result, dict) and "destination" in exec_result:
                    state.artifacts_created.append(exec_result["destination"])

                # Error loop detection
                is_error = isinstance(exec_result, dict) and (
                    "error" in exec_result or not exec_result.get("success", True)
                )
                if is_error:
                    consecutive_tool_errors += 1
                    if consecutive_tool_errors >= self.policy.max_consecutive_errors:
                        raise InfiniteLoopDetectedException(
                            f"Circuit breaker triggered: {consecutive_tool_errors} consecutive tool execution errors encountered without resolution."
                        )
                else:
                    consecutive_tool_errors = 0

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
