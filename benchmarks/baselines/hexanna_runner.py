import os
import time
from typing import Dict, Any, List
from hexanna.adapters.engine.duckdb_adapter import DuckDBAdapter
from hexanna.tools.schema_inspector import SchemaInspectorTool
from hexanna.tools.out_of_core_sql import OutOfCoreSQLTool
from hexanna.tools.profile_sketcher import ProfileSketcherTool
from hexanna.harness.runtime import HexannaRuntime
from hexanna.ports.llm_gateway import ILLMGateway

class BenchmarkMockGateway(ILLMGateway):
    """Deterministic LLM reasoning simulator for reproducible benchmarking."""
    def __init__(self, responses: List[Dict[str, Any]]):
        self.responses = list(responses)
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def call_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], temperature: float = 0.0) -> Dict[str, Any]:
        # Quantify wire size in tokens
        msg_str = str(messages) + str(tools_schema)
        # Approximate tokens as len(msg_str) / 4
        current_prompt_tokens = max(1, len(msg_str) // 4)
        self.prompt_tokens += current_prompt_tokens

        resp = self.responses.pop(0) if self.responses else {"role": "assistant", "content": "Done", "tool_calls": []}
        resp_str = str(resp)
        self.completion_tokens += max(1, len(resp_str) // 4)
        return resp

class HexannaBenchmarkRunner:
    """
    Evaluates Hexanna IIVX agentic harness across the 3 benchmark query profiles.
    Captures orchestration overhead, token metrics, and memory bounds with disk spilling.
    """

    def __init__(self, data_dir: str, memory_limit: str = "2GB", enable_profile_sketcher: bool = True):
        self.data_dir = data_dir
        self.memory_limit = memory_limit
        self.enable_profile_sketcher = enable_profile_sketcher

        self.engine = DuckDBAdapter(memory_limit=self.memory_limit)
        self.inspector = SchemaInspectorTool(self.engine)
        self.sql_tool = OutOfCoreSQLTool(self.engine)
        self.tools = [self.inspector, self.sql_tool]

        if self.enable_profile_sketcher:
            self.sketcher = ProfileSketcherTool(self.engine)
            self.tools.append(self.sketcher)

    def run_profile_a_scan_agg(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q6 Forecasting Revenue Change."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        sql = f"""
        SELECT sum(l_extendedprice * l_discount) as revenue
        FROM '{lineitem_p}'
        WHERE l_shipdate >= DATE '1994-01-01' AND l_shipdate < DATE '1995-01-01'
        AND l_discount BETWEEN 0.05 AND 0.07 AND l_quantity < 24
        """
        simulated_turns = [
            {
                "role": "assistant",
                "content": "Inspecting lineitem dataset schema first.",
                "tool_calls": [{"id": "call_1", "name": "inspect_dataset_schema", "arguments": {"file_path": lineitem_p}}]
            },
            {
                "role": "assistant",
                "content": "Executing out-of-core transformation.",
                "tool_calls": [{"id": "call_2", "name": "execute_out_of_core_sql", "arguments": {"query": sql, "output_path": output_path}}]
            },
            {
                "role": "assistant",
                "content": "Task completed successfully.",
                "tool_calls": []
            }
        ]
        gateway = BenchmarkMockGateway(simulated_turns)
        runtime = HexannaRuntime(llm_gateway=gateway, tools=self.tools)

        start = time.perf_counter()
        state = runtime.run(f"Filter revenue change in {lineitem_p} to {output_path}")
        elapsed = time.perf_counter() - start

        return {
            "status": "success" if state.completed else "failed",
            "profile": "Profile-A (Scan/Agg)",
            "iterations": state.iteration,
            "wall_clock_sec": elapsed,
            "prompt_tokens": gateway.prompt_tokens,
            "completion_tokens": gateway.completion_tokens,
            "artifacts": state.artifacts_created
        }

    def run_profile_b_multiway_join(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q5 Local Supplier Volume Query."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        orders_p = os.path.join(self.data_dir, "orders.parquet")
        customer_p = os.path.join(self.data_dir, "customer.parquet")
        supplier_p = os.path.join(self.data_dir, "supplier.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        sql = f"""
        SELECT c.c_nationkey, sum(l.l_extendedprice * (1 - l.l_discount)) as revenue
        FROM '{customer_p}' c
        JOIN '{orders_p}' o ON c.c_custkey = o.o_custkey
        JOIN '{lineitem_p}' l ON l.l_orderkey = o.o_orderkey
        JOIN '{supplier_p}' s ON l.l_suppkey = s.s_suppkey
        WHERE o.o_orderdate >= DATE '1994-01-01' AND o.o_orderdate < DATE '1995-01-01'
        GROUP BY c.c_nationkey ORDER BY revenue DESC
        """
        simulated_turns = [
            {
                "role": "assistant",
                "content": "Inspecting schema for multiway join.",
                "tool_calls": [{"id": "call_1", "name": "inspect_dataset_schema", "arguments": {"file_path": orders_p}}]
            },
            {
                "role": "assistant",
                "content": "Executing 5-way out-of-core join.",
                "tool_calls": [{"id": "call_2", "name": "execute_out_of_core_sql", "arguments": {"query": sql, "output_path": output_path}}]
            },
            {
                "role": "assistant",
                "content": "Multiway join persisted.",
                "tool_calls": []
            }
        ]
        gateway = BenchmarkMockGateway(simulated_turns)
        runtime = HexannaRuntime(llm_gateway=gateway, tools=self.tools)

        start = time.perf_counter()
        state = runtime.run(f"Execute multiway supplier join to {output_path}")
        elapsed = time.perf_counter() - start

        return {
            "status": "success" if state.completed else "failed",
            "profile": "Profile-B (Multi-Join)",
            "iterations": state.iteration,
            "wall_clock_sec": elapsed,
            "prompt_tokens": gateway.prompt_tokens,
            "completion_tokens": gateway.completion_tokens,
            "artifacts": state.artifacts_created
        }

    def run_profile_c_subquery_window(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q17 Small-Quantity-Order Revenue Query."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        part_p = os.path.join(self.data_dir, "part.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        sql = f"""
        SELECT sum(l.l_extendedprice) / 7.0 as avg_yearly
        FROM '{lineitem_p}' l
        JOIN '{part_p}' p ON p.p_partkey = l.l_partkey
        WHERE l.l_quantity < (
            SELECT 0.2 * avg(l2.l_quantity)
            FROM '{lineitem_p}' l2
            WHERE l2.l_partkey = p.p_partkey
        )
        """
        simulated_turns = [
            {
                "role": "assistant",
                "content": "Inspecting schema.",
                "tool_calls": [{"id": "call_1", "name": "inspect_dataset_schema", "arguments": {"file_path": part_p}}]
            },
            {
                "role": "assistant",
                "content": "Executing correlated subquery pipeline.",
                "tool_calls": [{"id": "call_2", "name": "execute_out_of_core_sql", "arguments": {"query": sql, "output_path": output_path}}]
            },
            {
                "role": "assistant",
                "content": "Subquery execution complete.",
                "tool_calls": []
            }
        ]
        gateway = BenchmarkMockGateway(simulated_turns)
        runtime = HexannaRuntime(llm_gateway=gateway, tools=self.tools)

        start = time.perf_counter()
        state = runtime.run(f"Execute small-quantity subquery to {output_path}")
        elapsed = time.perf_counter() - start

        return {
            "status": "success" if state.completed else "failed",
            "profile": "Profile-C (Subquery/Window)",
            "iterations": state.iteration,
            "wall_clock_sec": elapsed,
            "prompt_tokens": gateway.prompt_tokens,
            "completion_tokens": gateway.completion_tokens,
            "artifacts": state.artifacts_created
        }

    def close(self):
        self.engine.close()
