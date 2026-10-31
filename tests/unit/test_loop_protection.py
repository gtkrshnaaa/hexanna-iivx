import pytest
from typing import Type
from pydantic import BaseModel
from hexanna.harness.runtime import HexannaRuntime
from hexanna.domain.policies import ResourcePolicy
from hexanna.domain.exceptions import InfiniteLoopDetectedException
from hexanna.tools.base import BaseTool
from hexanna.adapters.llm.openai_client import OpenAIGateway

class DummyArgs(BaseModel):
    step: int

class DummyTool(BaseTool):
    name: str = "dummy_tool"
    description: str = "A dummy tool for testing loop protection."
    args_schema: Type[BaseModel] = DummyArgs

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def execute(self, step: int):
        if self.should_fail:
            return {"error": "Simulated tool execution failure", "success": False}
        return {"result": f"step-{step}", "success": True}

class InfiniteNewCallGateway:
    """Simulates an infinite sequence of distinct tool calls."""
    def __init__(self):
        self.call_count = 0

    def call_with_tools(self, messages, tools_schema, temperature=0.0):
        self.call_count += 1
        return {
            "role": "assistant",
            "content": f"Iteration {self.call_count}",
            "tool_calls": [
                {
                    "id": f"call_{self.call_count}",
                    "name": "dummy_tool",
                    "arguments": {"step": self.call_count}
                }
            ]
        }

class CyclicIdenticalCallGateway:
    """Simulates an agent stuck in a loop calling the exact same tool repeatedly."""
    def call_with_tools(self, messages, tools_schema, temperature=0.0):
        return {
            "role": "assistant",
            "content": "Stuck in repetitive loop",
            "tool_calls": [
                {
                    "id": "fixed_call_id",
                    "name": "dummy_tool",
                    "arguments": {"step": 42}
                }
            ]
        }

def test_circuit_breaker_max_api_calls():
    policy = ResourcePolicy(max_api_calls=5, absolute_max_iterations=20)
    gateway = InfiniteNewCallGateway()
    runtime = HexannaRuntime(
        llm_gateway=gateway,
        tools=[DummyTool(should_fail=False)],
        policy=policy
    )

    with pytest.raises(InfiniteLoopDetectedException) as exc_info:
        runtime.run("Run forever", max_iterations=20)

    assert "exceeded maximum allowed API calls" in str(exc_info.value)
    assert gateway.call_count == 5

def test_circuit_breaker_cyclic_identical_tool_calls():
    policy = ResourcePolicy(max_consecutive_identical_calls=3)
    gateway = CyclicIdenticalCallGateway()
    runtime = HexannaRuntime(
        llm_gateway=gateway,
        tools=[DummyTool(should_fail=False)],
        policy=policy
    )

    with pytest.raises(InfiniteLoopDetectedException) as exc_info:
        runtime.run("Infinite cyclic task", max_iterations=10)

    assert "detected cyclic loop with identical tool calls" in str(exc_info.value)

def test_circuit_breaker_consecutive_tool_errors():
    policy = ResourcePolicy(max_consecutive_errors=3)
    gateway = InfiniteNewCallGateway()
    runtime = HexannaRuntime(
        llm_gateway=gateway,
        tools=[DummyTool(should_fail=True)],
        policy=policy
    )

    with pytest.raises(InfiniteLoopDetectedException) as exc_info:
        runtime.run("Failing pipeline", max_iterations=10)

    assert "consecutive tool execution errors encountered" in str(exc_info.value)

def test_iterations_bounded_by_absolute_max():
    policy = ResourcePolicy(absolute_max_iterations=4, max_api_calls=15)
    gateway = InfiniteNewCallGateway()
    runtime = HexannaRuntime(
        llm_gateway=gateway,
        tools=[DummyTool(should_fail=False)],
        policy=policy
    )

    state = runtime.run("Bounded iterations", max_iterations=100)
    assert state.max_iterations == 4
    assert state.iteration == 4

def test_openai_gateway_timeout_configuration():
    gateway = OpenAIGateway(api_key="test-key", timeout=45.0)
    assert gateway.timeout == 45.0
    assert gateway.client.timeout == 45.0
