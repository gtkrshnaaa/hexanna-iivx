import os
import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from hexanna.ports.llm_gateway import ILLMGateway
from hexanna.domain.policies import ResourcePolicy

class OpenAIGateway(ILLMGateway):
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: str = "llama-3.3-70b-versatile",
        timeout: Optional[float] = None
    ):
        self.timeout = timeout or ResourcePolicy.api_request_timeout
        resolved_key = api_key
        resolved_url = base_url

        if not resolved_key or not resolved_url:
            model_lower = model_name.lower()
            if "deepseek" in model_lower:
                resolved_key = resolved_key or os.getenv("DEEPSEEK_API_KEY")
                resolved_url = resolved_url or os.getenv("DEEPSEEK_BASE_URL")
            elif "gemini" in model_lower:
                resolved_key = resolved_key or os.getenv("GEMINI_API_KEY")
                resolved_url = resolved_url or os.getenv("GEMINI_BASE_URL")

            # Check local benchmark models.json configuration if still unresolved
            if not resolved_key or not resolved_url:
                candidate_paths = [
                    os.path.join(os.getcwd(), "benchmarks", "local", "models.json"),
                    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "benchmarks", "local", "models.json")
                ]
                for p in candidate_paths:
                    if os.path.exists(p):
                        try:
                            with open(p, "r", encoding="utf-8") as f:
                                cfg = json.load(f)
                                for model_family in ("deepseek", "gemini"):
                                    if model_family in cfg and (
                                        model_family in model_lower or cfg[model_family].get("model_id") == model_name
                                    ):
                                        resolved_key = resolved_key or cfg[model_family].get("api_key")
                                        resolved_url = resolved_url or cfg[model_family].get("base_url")
                        except Exception:
                            pass
                        break

        self.client = OpenAI(
            api_key=resolved_key or os.getenv("LLM_API_KEY", "EMPTY"),
            base_url=resolved_url or os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            timeout=self.timeout
        )
        self.model_name = model_name

    def call_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: List[Dict[str, Any]],
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        max_retries = 3
        backoff = 2.0

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools_schema if tools_schema else None,
                    tool_choice="auto" if tools_schema else None,
                    temperature=temperature,
                    timeout=self.timeout
                )
                choice = response.choices[0]
                message = choice.message

                tool_calls_data = []
                if message.tool_calls:
                    for tc in message.tool_calls:
                        args = (
                            json.loads(tc.function.arguments)
                            if isinstance(tc.function.arguments, str)
                            else tc.function.arguments
                        )
                        tool_calls_data.append({
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": args
                        })

                usage_data = {}
                if response.usage:
                    usage_data = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }

                return {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": tool_calls_data,
                    "usage": usage_data
                }
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(min(backoff ** attempt, 10.0))
