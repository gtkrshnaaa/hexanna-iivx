import os
import sys
import time
import json
import argparse
from typing import Optional, Dict, Any

from hexanna.adapters.engine.duckdb_adapter import DuckDBAdapter
from hexanna.adapters.llm.openai_client import OpenAIGateway
from hexanna.adapters.storage.sqlite_history import SQLiteChatHistory
from hexanna.tools.schema_inspector import SchemaInspectorTool
from hexanna.tools.out_of_core_sql import OutOfCoreSQLTool
from hexanna.tools.profile_sketcher import ProfileSketcherTool
from hexanna.harness.runtime import HexannaRuntime
from hexanna.tui.repl import HexannaREPL
from hexanna.domain.exceptions import InfiniteLoopDetectedException

def resolve_runtime_config(args: argparse.Namespace, history_db: Optional[SQLiteChatHistory] = None) -> Dict[str, Any]:
    """Resolves configuration hierarchically: CLI -> Env -> SQLite -> Local Config -> Fallback."""
    saved_cfg = history_db.get_all_config() if history_db else {}

    # Model resolution
    cli_model = getattr(args, "model", None)
    env_model = os.getenv("LLM_MODEL") or os.getenv("DEEPSEEK_MODEL") or os.getenv("GEMINI_MODEL")
    db_model = saved_cfg.get("model_name") or saved_cfg.get("model")

    local_default = None
    local_cfg = os.path.join(os.getcwd(), "benchmarks", "local", "models.json")
    if os.path.exists(local_cfg):
        try:
            with open(local_cfg, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "gemini" in data and data["gemini"].get("model_id"):
                    local_default = data["gemini"]["model_id"]
                elif "deepseek" in data and data["deepseek"].get("model_id"):
                    local_default = data["deepseek"]["model_id"]
        except Exception:
            pass

    resolved_model = cli_model or env_model or db_model or local_default or "llama-3.3-70b-versatile"

    # Memory limit resolution
    cli_mem = getattr(args, "max_memory", None)
    env_mem = os.getenv("HEXANNA_MAX_MEMORY")
    db_mem = saved_cfg.get("memory_limit")
    resolved_mem = cli_mem or env_mem or db_mem or "2GB"

    # Base URL & API Key
    cli_base_url = getattr(args, "base_url", None) or saved_cfg.get("base_url")
    cli_api_key = getattr(args, "api_key", None) or saved_cfg.get("api_key")

    return {
        "model": resolved_model,
        "max_memory": resolved_mem,
        "base_url": cli_base_url,
        "api_key": cli_api_key
    }

def read_input_or_stdin(val: Optional[str], label: str = "input") -> str:
    """Reads positional argument value or reads from sys.stdin when val is '-'."""
    if val == "-" or (val is None and not sys.stdin.isatty()):
        content = sys.stdin.read().strip()
        if not content:
            sys.stderr.write(f"Error: Empty {label} received from standard input.\n")
            sys.exit(2)
        return content
    if not val:
        sys.stderr.write(f"Error: Missing required {label}.\n")
        sys.exit(2)
    return val

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hexanna",
        description="Hexanna IIVX: Deterministic Out-of-Core Data Engineering Agent Harness"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: repl
    repl_p = subparsers.add_parser("repl", help="Launch interactive TUI REPL session")
    repl_p.add_argument("--model", type=str, default=None, help="Model name")
    repl_p.add_argument("--max-memory", type=str, default=None, help="DuckDB memory ceiling")
    repl_p.add_argument("--base-url", type=str, default=None, help="Remote OpenAI-compatible base URL")
    repl_p.add_argument("--api-key", type=str, default=None, help="Remote API key")

    # Command: run (headless agent loop)
    run_p = subparsers.add_parser("run", help="Execute an autonomous goal in headless mode")
    run_p.add_argument("objective", nargs="?", default=None, help="Natural language objective (or '-' for stdin)")
    run_p.add_argument("--model", type=str, default=None, help="Inference model name")
    run_p.add_argument("--max-memory", type=str, default=None, help="DuckDB memory ceiling (e.g. 2GB)")
    run_p.add_argument("--max-iterations", type=int, default=10, help="Max ReAct iterations")
    run_p.add_argument("--session-id", type=str, default=None, help="Custom session identifier")
    run_p.add_argument("--base-url", type=str, default=None, help="Remote OpenAI-compatible base URL")
    run_p.add_argument("--api-key", type=str, default=None, help="Remote API key")
    run_p.add_argument("--json", action="store_true", help="Emit structured machine-readable JSON")
    run_p.add_argument("-q", "--quiet", action="store_true", help="Suppress human banner and progress output")

    # Command: query
    query_p = subparsers.add_parser("query", help="Execute out-of-core SQL query to disk")
    query_p.add_argument("sql", nargs="?", default=None, help="DuckDB SQL statement (or '-' for stdin)")
    query_p.add_argument("output", type=str, help="Destination Parquet path")
    query_p.add_argument("--max-memory", type=str, default=None, help="DuckDB memory ceiling")
    query_p.add_argument("--json", action="store_true", help="Emit JSON result summary")
    query_p.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")

    # Command: inspect
    inspect_p = subparsers.add_parser("inspect", help="Inspect dataset schema without loading data")
    inspect_p.add_argument("file_path", type=str, help="Path to CSV or Parquet file")

    # Command: profile
    profile_p = subparsers.add_parser("profile", help="Compute summary sketch for a column")
    profile_p.add_argument("file_path", type=str, help="Target dataset path")
    profile_p.add_argument("column", type=str, help="Column name to profile")

    # Command: history, sessions, artifacts
    hist_p = subparsers.add_parser("history", help="List recent commands from SQLite history")
    hist_p.add_argument("--limit", type=int, default=20, help="Number of records to show")

    sess_p = subparsers.add_parser("sessions", help="List saved chat sessions from SQLite history")
    sess_p.add_argument("--limit", type=int, default=20, help="Number of sessions to show")

    art_p = subparsers.add_parser("artifacts", help="List generated out-of-core dataset artifacts")
    art_p.add_argument("--limit", type=int, default=20, help="Number of artifacts to show")

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    history_db = SQLiteChatHistory()

    try:
        if not args.command or args.command == "repl":
            cfg = resolve_runtime_config(args, history_db)
            repl = HexannaREPL(
                memory_limit=cfg["max_memory"],
                model_name=cfg["model"],
                base_url=cfg["base_url"],
                api_key=cfg["api_key"]
            )
            repl.run()
            sys.exit(0)

        elif args.command == "history":
            records = history_db.list_commands(limit=args.limit)
            print(json.dumps(records, indent=2))
            sys.exit(0)

        elif args.command == "sessions":
            sessions = [
                {
                    "session_id": s.session_id,
                    "title": s.title,
                    "messages": s.message_count,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at
                }
                for s in history_db.list_sessions(limit=args.limit)
            ]
            print(json.dumps(sessions, indent=2))
            sys.exit(0)

        elif args.command == "artifacts":
            records = history_db.list_artifacts(limit=args.limit)
            print(json.dumps(records, indent=2))
            sys.exit(0)

        elif args.command == "inspect":
            engine = DuckDBAdapter()
            try:
                tool = SchemaInspectorTool(engine)
                res = tool.execute(file_path=args.file_path)
                print(json.dumps(res, indent=2))
                sys.exit(0)
            finally:
                engine.close()

        elif args.command == "profile":
            engine = DuckDBAdapter()
            try:
                tool = ProfileSketcherTool(engine)
                res = tool.execute(file_path=args.file_path, column_name=args.column)
                print(json.dumps(res, indent=2))
                sys.exit(0)
            finally:
                engine.close()

        elif args.command == "query":
            cfg = resolve_runtime_config(args, history_db)
            sql_query = read_input_or_stdin(args.sql, "SQL statement")
            engine = DuckDBAdapter(memory_limit=cfg["max_memory"])
            tool = OutOfCoreSQLTool(engine)
            try:
                res = tool.execute(query=sql_query, output_path=args.output)
                history_db.record_artifact(
                    session_id=f"query_{int(time.time())}",
                    artifact_path=res["destination"],
                    file_size_bytes=res.get("output_size_bytes"),
                    row_count=res.get("rows_written")
                )
                if args.json:
                    print(json.dumps(res, indent=2))
                elif not args.quiet:
                    mb = res.get("output_size_bytes", 0) / (1024 * 1024)
                    print(f"[OK] Persisted {res['rows_written']} rows to {res['destination']} ({mb:.2f} MB)")
                sys.exit(0)
            except Exception as err:
                sys.stderr.write(f"[ERROR] Query execution failed: {err}\n")
                sys.exit(1)
            finally:
                engine.close()

        elif args.command == "run":
            cfg = resolve_runtime_config(args, history_db)
            objective = read_input_or_stdin(args.objective, "objective")
            session_id = args.session_id or f"run_{int(time.time())}"

            engine = DuckDBAdapter(memory_limit=cfg["max_memory"])
            tools = [
                SchemaInspectorTool(engine),
                OutOfCoreSQLTool(engine),
                ProfileSketcherTool(engine)
            ]
            gateway = OpenAIGateway(
                model_name=cfg["model"],
                base_url=cfg["base_url"],
                api_key=cfg["api_key"]
            )
            runtime = HexannaRuntime(
                llm_gateway=gateway,
                tools=tools,
                history_repo=history_db
            )

            if not args.quiet and not args.json:
                print(f"[*] Starting Hexanna IIVX headless execution for objective: '{objective}'")
                print(f"[*] Engine Memory: {cfg['max_memory']} | Model: {cfg['model']}")

            try:
                state = runtime.run(objective, max_iterations=args.max_iterations, session_id=session_id)

                for art in state.artifacts_created:
                    if os.path.exists(art):
                        history_db.record_artifact(
                            session_id=session_id,
                            artifact_path=art,
                            file_size_bytes=os.path.getsize(art)
                        )

                if args.json:
                    payload = {
                        "task_id": state.task_id,
                        "objective": state.objective,
                        "status": "success" if state.completed else "incomplete",
                        "completed": state.completed,
                        "iterations": state.iteration,
                        "api_calls": state.api_calls,
                        "artifacts": state.artifacts_created,
                        "history": state.history
                    }
                    print(json.dumps(payload, indent=2))
                elif not args.quiet:
                    status_lbl = "Completed" if state.completed else "Incomplete"
                    print(f"[*] Execution finished: {status_lbl} (Iterations: {state.iteration}, API Calls: {state.api_calls})")
                    if state.artifacts_created:
                        print(f"[*] Artifacts created: {state.artifacts_created}")

                sys.exit(0 if state.completed else 1)

            except InfiniteLoopDetectedException as loop_err:
                if args.json:
                    print(json.dumps({
                        "task_id": session_id,
                        "objective": objective,
                        "status": "circuit_breaker",
                        "completed": False,
                        "error": str(loop_err)
                    }, indent=2))
                else:
                    sys.stderr.write(f"[CIRCUIT BREAKER] {loop_err}\n")
                sys.exit(3)
            except Exception as err:
                if args.json:
                    print(json.dumps({
                        "task_id": session_id,
                        "objective": objective,
                        "status": "error",
                        "completed": False,
                        "error": str(err)
                    }, indent=2))
                else:
                    sys.stderr.write(f"[ERROR] {err}\n")
                sys.exit(1)
            finally:
                engine.close()

    finally:
        history_db.close()

if __name__ == "__main__":
    main()
