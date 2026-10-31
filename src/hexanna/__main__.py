import argparse
import sys
import json
from hexanna.adapters.engine.duckdb_adapter import DuckDBAdapter
from hexanna.adapters.llm.openai_client import OpenAIGateway
from hexanna.tools.schema_inspector import SchemaInspectorTool
from hexanna.tools.out_of_core_sql import OutOfCoreSQLTool
from hexanna.tools.profile_sketcher import ProfileSketcherTool
from hexanna.harness.runtime import HexannaRuntime

def main():
    parser = argparse.ArgumentParser(
        prog="hexanna",
        description="Hexanna IIVX: Deterministic Out-of-Core Data Engineering Agent Harness"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Execute an autonomous goal")
    run_parser.add_argument("objective", type=str, help="Natural language objective")
    run_parser.add_argument("--model", type=str, default="llama-3.3-70b-versatile", help="Model name")
    run_parser.add_argument("--max-memory", type=str, default="2GB", help="DuckDB memory ceiling")
    run_parser.add_argument("--max-iterations", type=int, default=10, help="Max ReAct iterations")

    # Command: inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect dataset schema without loading data")
    inspect_parser.add_argument("file_path", type=str, help="Path to CSV or Parquet file")

    # Command: profile
    profile_parser = subparsers.add_parser("profile", help="Compute summary sketch for a column")
    profile_parser.add_argument("file_path", type=str, help="Target dataset path")
    profile_parser.add_argument("column", type=str, help="Column name to profile")

    # Command: query
    query_parser = subparsers.add_parser("query", help="Execute out-of-core SQL query to disk")
    query_parser.add_argument("sql", type=str, help="DuckDB SQL statement")
    query_parser.add_argument("output", type=str, help="Destination Parquet path")
    query_parser.add_argument("--max-memory", type=str, default="2GB", help="DuckDB memory ceiling")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "inspect":
        engine = DuckDBAdapter()
        tool = SchemaInspectorTool(engine)
        res = tool.execute(file_path=args.file_path)
        print(json.dumps(res, indent=2))
        engine.close()

    elif args.command == "profile":
        engine = DuckDBAdapter()
        tool = ProfileSketcherTool(engine)
        res = tool.execute(file_path=args.file_path, column_name=args.column)
        print(json.dumps(res, indent=2))
        engine.close()

    elif args.command == "query":
        engine = DuckDBAdapter(memory_limit=args.max_memory)
        tool = OutOfCoreSQLTool(engine)
        res = tool.execute(query=args.sql, output_path=args.output)
        print(json.dumps(res, indent=2))
        engine.close()

    elif args.command == "run":
        engine = DuckDBAdapter(memory_limit=args.max_memory)
        tools = [
            SchemaInspectorTool(engine),
            OutOfCoreSQLTool(engine),
            ProfileSketcherTool(engine)
        ]
        gateway = OpenAIGateway(model_name=args.model)
        runtime = HexannaRuntime(llm_gateway=gateway, tools=tools)
        print(f"[*] Starting Hexanna IIVX execution for objective: '{args.objective}'")
        state = runtime.run(args.objective, max_iterations=args.max_iterations)
        print(f"[*] Execution finished. Completed: {state.completed}, Iterations: {state.iteration}")
        if state.artifacts_created:
            print(f"[*] Artifacts created: {state.artifacts_created}")
        engine.close()

if __name__ == "__main__":
    main()
