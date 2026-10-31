import os
import sys
import time
import glob
import readline
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn

from hexanna.adapters.engine.duckdb_adapter import DuckDBAdapter
from hexanna.adapters.llm.openai_client import OpenAIGateway
from hexanna.adapters.storage.sqlite_history import SQLiteChatHistory
from hexanna.adapters.telemetry.psutil_tracker import PsutilTracker
from hexanna.tools.schema_inspector import SchemaInspectorTool
from hexanna.tools.out_of_core_sql import OutOfCoreSQLTool
from hexanna.tools.profile_sketcher import ProfileSketcherTool
from hexanna.harness.runtime import HexannaRuntime
from hexanna.domain.exceptions import HexannaDomainException, InfiniteLoopDetectedException

HISTORY_FILE = os.path.expanduser("~/.hexanna_history")

class HexannaCompleter:
    """Readline tab-completer for slash commands and local file paths."""

    COMMANDS = [
        "/help",
        "/inspect",
        "/profile",
        "/sql",
        "/run",
        "/sessions",
        "/history",
        "/history-chat",
        "/clear-history",
        "/artifacts",
        "/memory",
        "/stats",
        "/config",
        "/clear",
        "/exit",
        "/quit"
    ]

    def complete(self, text: str, state: int) -> Optional[str]:
        line = readline.get_line_buffer()
        cursor_pos = readline.get_begidx()

        # Command completion
        if cursor_pos == 0:
            options = [cmd for cmd in self.COMMANDS if cmd.startswith(text)]
            if state < len(options):
                return options[state]
            return None

        # Path completion for arguments
        prefix = text or ""
        expanded = os.path.expanduser(prefix)
        matches = glob.glob(expanded + "*")
        formatted = []
        for match in matches:
            if os.path.isdir(match):
                formatted.append(match + "/")
            else:
                formatted.append(match)
        if state < len(formatted):
            return formatted[state]
        return None

class HexannaREPL:
    """Professional interactive Terminal REPL for Hexanna IIVX."""

    def __init__(
        self,
        memory_limit: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        db_path: Optional[str] = None
    ):
        self.console = Console()
        self.history_db = SQLiteChatHistory(db_path=db_path) if db_path else SQLiteChatHistory()
        saved_config = self.history_db.get_all_config()

        self.memory_limit = memory_limit or saved_config.get("memory_limit") or "2GB"
        self.model_name = model_name or saved_config.get("model_name") or saved_config.get("model") or "llama-3.3-70b-versatile"
        self.base_url = base_url or saved_config.get("base_url") or os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
        self.api_key = api_key or saved_config.get("api_key") or os.getenv("LLM_API_KEY", "")
        self.engine = DuckDBAdapter(memory_limit=self.memory_limit)
        self.telemetry = PsutilTracker()

        self.session_id = f"session_{int(time.time())}"
        self.history_db.create_session(self.session_id, f"Interactive Session {self.session_id}")

        # Tools
        self.tool_inspector = SchemaInspectorTool(self.engine)
        self.tool_sql = OutOfCoreSQLTool(self.engine)
        self.tool_profile = ProfileSketcherTool(self.engine)
        self.tools = [self.tool_inspector, self.tool_sql, self.tool_profile]

        self._running = False
        self._setup_readline()

    def _setup_readline(self):
        completer = HexannaCompleter()
        readline.set_completer(completer.complete)
        readline.parse_and_bind("tab: complete")
        readline.set_completer_delims(" \t\n`~!@#$%^&*()=+[{]}\\|;:'\",<>?")
        if os.path.exists(HISTORY_FILE):
            try:
                readline.read_history_file(HISTORY_FILE)
            except Exception:
                pass

    def _save_history(self):
        try:
            readline.write_history_file(HISTORY_FILE)
        except Exception:
            pass

    def _get_rss_mb(self) -> float:
        stats = self.telemetry.sample()
        return stats.get("rss_mb", 0.0)

    def print_banner(self):
        rss = self._get_rss_mb()
        banner_text = Text()
        banner_text.append("HEXANNA IIVX", style="bold white")
        banner_text.append(" :: ", style="bright_black")
        banner_text.append("Deterministic Out-of-Core Agent Harness\n", style="cyan")
        banner_text.append(f"Engine: DuckDB [Cap: {self.memory_limit}] | Model: {self.model_name}\n", style="white")
        banner_text.append(f"Host Memory RSS: {rss:.1f} MB | Temp Spill: {self.engine.temp_directory}", style="bright_black")

        panel = Panel(
            banner_text,
            border_style="cyan",
            expand=False,
            padding=(0, 2)
        )
        self.console.print(panel)
        self.console.print("[bright_black]Type [bold white]/help[/bold white] for command list or start with [bold white]/inspect[/bold white], [bold white]/sql[/bold white], or natural queries.[/bright_black]\n")

    def cmd_help(self):
        table = Table(title="Hexanna IIVX REPL Commands", border_style="bright_black", show_header=True)
        table.add_column("Command", style="bold cyan", width=18)
        table.add_column("Arguments", style="white", width=24)
        table.add_column("Description", style="bright_black")

        table.add_row("/help", "", "Show this commands reference")
        table.add_row("/inspect", "<file_path>", "Inspect dataset schema and cardinality without loading RAM")
        table.add_row("/profile", "<file_path> <column>", "Compute statistical sketches (nulls, quantiles, distincts)")
        table.add_row("/sql", "<query> [out.parquet]", "Execute out-of-core SQL (previews table or streams to disk)")
        table.add_row("/run", "<objective>", "Launch autonomous ReAct agent loop for a goal")
        table.add_row("/sessions", "[limit]", "List historical chat sessions stored in SQLite")
        table.add_row("/history", "[limit]", "Display recent command history from SQLite database")
        table.add_row("/history-chat", "[session_id]", "Display message turns for a chat session from SQLite")
        table.add_row("/clear-history", "", "Purge all historical chat sessions and commands in SQLite")
        table.add_row("/artifacts", "[limit]", "List generated out-of-core dataset artifacts in SQLite")
        table.add_row("/memory", "", "Display process memory metrics and DuckDB disk spill stats")
        table.add_row("/config", "[key] [value]", "View or update model, memory limit, or base URL in SQLite")
        table.add_row("/clear", "", "Clear terminal screen and reprint banner")
        table.add_row("/exit", "", "Exit REPL session cleanly")
        self.console.print(table)

    def cmd_inspect(self, args: str):
        path = args.strip().strip("'\"")
        if not path:
            self.console.print("[red][ERROR][/red] File path required: /inspect <file_path>")
            return
        if not os.path.exists(path):
            self.console.print(f"[red][ERROR][/red] Dataset not found at: {path}")
            return

        with self.console.status(f"[cyan]Inspecting {path}...[/cyan]"):
            try:
                res = self.tool_inspector.execute(file_path=path)
            except Exception as err:
                self.console.print(f"[red][ERROR][/red] Inspection failed: {err}")
                return

        # Summary Header
        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style="bold white")
        info_table.add_column(style="cyan")
        info_table.add_row("File Target:", res["file_path"])
        info_table.add_row("Total Rows:", f"{res['total_rows']:,}")
        info_table.add_row("Columns:", str(res["total_columns"]))
        info_table.add_row("File Size:", f"{res['size_mb']} MB")
        self.console.print(Panel(info_table, title="[bold cyan]Dataset Overview[/bold cyan]", border_style="bright_black"))

        # Column Schema Table
        col_table = Table(title="Relational Schema", border_style="bright_black", show_lines=True)
        col_table.add_column("#", style="bright_black", width=4)
        col_table.add_column("Column Name", style="bold white")
        col_table.add_column("DuckDB Data Type", style="cyan")

        for idx, col in enumerate(res["columns"], start=1):
            col_table.add_row(str(idx), col["name"], col["type"])
        self.console.print(col_table)

    def cmd_profile(self, args: str):
        parts = args.strip().split()
        if len(parts) < 2:
            self.console.print("[red][ERROR][/red] Missing arguments: /profile <file_path> <column_name>")
            return
        file_path, col_name = parts[0].strip("'\""), parts[1].strip("'\"")

        with self.console.status(f"[cyan]Profiling column '{col_name}'...[/cyan]"):
            try:
                res = self.tool_profile.execute(file_path=file_path, column_name=col_name)
            except Exception as err:
                self.console.print(f"[red][ERROR][/red] Profiling failed: {err}")
                return

        table = Table(title=f"Statistical Sketches :: {col_name}", border_style="bright_black")
        table.add_column("Metric", style="bold white", width=22)
        table.add_column("Value", style="cyan")

        for key, val in res.items():
            formatted_val = f"{val:,}" if isinstance(val, int) else str(val)
            table.add_row(key.replace("_", " ").title(), formatted_val)
        self.console.print(table)

    def cmd_sql(self, args: str):
        raw = args.strip()
        if not raw:
            self.console.print("[red][ERROR][/red] SQL expression required: /sql <query> [output_path.parquet]")
            return

        # Check for destination file argument
        out_path = None
        sql_query = raw
        if " -> " in raw:
            sql_query, out_path = raw.split(" -> ", 1)
            sql_query, out_path = sql_query.strip(), out_path.strip().strip("'\"")

        if out_path:
            with self.console.status(f"[cyan]Streaming out-of-core transformation to {out_path}...[/cyan]"):
                try:
                    res = self.tool_sql.execute(query=sql_query, output_path=out_path)
                    self.history_db.record_artifact(
                        session_id=self.session_id,
                        artifact_path=res["destination"],
                        file_size_bytes=res.get("output_size_bytes"),
                        row_count=res.get("rows_written")
                    )
                    self.console.print(
                        f"[green][OK][/green] Persisted {res['rows_written']:,} rows to [cyan]{res['destination']}[/cyan] ({res['output_size_bytes'] / (1024*1024):.2f} MB)"
                    )
                except Exception as err:
                    self.console.print(f"[red][ERROR][/red] SQL execution failed: {err}")
            return

        # Terminal Preview Mode
        with self.console.status("[cyan]Executing analytical query...[/cyan]"):
            try:
                preview = self.engine.execute_preview(sql_query, limit=50)
            except Exception as err:
                self.console.print(f"[red][ERROR][/red] SQL error: {err}")
                return

        table = Table(border_style="bright_black", show_lines=True)
        for col in preview["columns"]:
            table.add_column(col, style="white")

        for row in preview["rows"]:
            table.add_row(*[str(val) if val is not None else "[bright_black]NULL[/bright_black]" for val in row])

        self.console.print(table)
        trunc_note = " (truncated at limit 50)" if preview["is_truncated"] else ""
        self.console.print(f"[bright_black]Returned {preview['row_count']} rows{trunc_note}[/bright_black]\n")

    @staticmethod
    def _censor_secret(val: Optional[str]) -> str:
        if not val or val == "EMPTY":
            return "[bright_black]Not Set[/bright_black]"
        return "[bright_black]****** (censored)[/bright_black]"

    def _sanitize_message(self, msg: str) -> str:
        sanitized = msg
        for secret in (self.api_key, self.base_url):
            if secret and len(secret) > 3:
                sanitized = sanitized.replace(secret, "****** (censored)")
        return sanitized

    def _scrub_sensitive_history(self):
        try:
            curr_len = readline.get_current_history_length()
            if curr_len > 0:
                last_item = readline.get_history_item(curr_len)
                if last_item and any(k in last_item.lower() for k in ("base_url", "api_key", "llm_api_key")):
                    readline.remove_history_item(curr_len - 1)
        except Exception:
            pass

    def cmd_run(self, objective: str):
        goal = objective.strip()
        if not goal:
            self.console.print("[red][ERROR][/red] Objective required: /run <natural language task>")
            return

        api_key = self.api_key or os.getenv("LLM_API_KEY")
        if not api_key:
            self.console.print("[yellow][WARN][/yellow] LLM_API_KEY is not set. Execution may fail if remote API requires authentication.")

        gateway = OpenAIGateway(model_name=self.model_name, base_url=self.base_url, api_key=api_key)
        runtime = HexannaRuntime(
            llm_gateway=gateway,
            tools=self.tools,
            history_repo=self.history_db
        )

        self.console.print(Rule(f"Autonomous Goal: {goal}", style="cyan"))

        with self.console.status("[cyan]Hexanna IIVX Agent is reasoning and executing...[/cyan]"):
            try:
                state = runtime.run(goal, session_id=self.session_id)
            except InfiniteLoopDetectedException as loop_err:
                err_msg = self._sanitize_message(str(loop_err))
                self.console.print(f"[bold red][CIRCUIT BREAKER][/bold red] {err_msg}")
                return
            except Exception as err:
                err_msg = self._sanitize_message(str(err))
                self.console.print(f"[red][ERROR][/red] Execution halted: {err_msg}")
                return

        # Display execution trace
        for step in state.history:
            tool_name = step.get("tool")
            args = step.get("args")
            output = step.get("output")
            iter_no = step.get("iteration")

            step_panel = Panel(
                f"[bold white]Arguments:[/bold white] {args}\n[bold white]Result:[/bold white] {output}",
                title=f"[cyan]Step {iter_no} :: {tool_name}[/cyan]",
                border_style="bright_black"
            )
            self.console.print(step_panel)

        status_text = "[green]SUCCESS[/green]" if state.completed else "[yellow]INCOMPLETE[/yellow]"
        self.console.print(f"[*] Task status: {status_text} | Total iterations: {state.iteration}")
        if state.artifacts_created:
            for art in state.artifacts_created:
                fsize = os.path.getsize(art) if os.path.exists(art) else None
                self.history_db.record_artifact(
                    session_id=self.session_id,
                    artifact_path=art,
                    file_size_bytes=fsize
                )
            self.console.print(f"[*] Generated artifacts: [cyan]{', '.join(state.artifacts_created)}[/cyan]")
        self.console.print(Rule(style="bright_black"))

    def cmd_sessions(self, args: str):
        limit = int(args.strip()) if args.strip().isdigit() else 20
        sessions = self.history_db.list_sessions(limit=limit)
        if not sessions:
            self.console.print("[bright_black]No saved sessions in SQLite history.[/bright_black]")
            return

        table = Table(title="SQLite Chat Sessions", border_style="bright_black", show_lines=True)
        table.add_column("Session ID", style="bold cyan")
        table.add_column("Title", style="white")
        table.add_column("Messages", style="cyan", justify="right")
        table.add_column("Updated", style="bright_black")

        for s in sessions:
            date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.updated_at))
            active_marker = " [bold green](active)[/bold green]" if s.session_id == self.session_id else ""
            table.add_row(f"{s.session_id}{active_marker}", s.title, str(s.message_count), date_str)
        self.console.print(table)

    def cmd_history(self, args: str):
        limit = int(args.strip()) if args.strip().isdigit() else 20
        commands = self.history_db.list_commands(limit=limit)
        if not commands:
            self.console.print("[bright_black]No recorded commands in SQLite history.[/bright_black]")
            return

        table = Table(title=f"SQLite Command History (Last {len(commands)})", border_style="bright_black")
        table.add_column("#", style="bright_black", width=4)
        table.add_column("Time", style="bright_black", width=19)
        table.add_column("Command", style="bold white")
        table.add_column("Status", style="cyan", width=10)

        for cmd in reversed(commands):
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cmd["created_at"]))
            status_style = "green" if cmd["status"] == "success" else "red"
            table.add_row(str(cmd["id"]), time_str, cmd["command_text"], f"[{status_style}]{cmd['status']}[/{status_style}]")
        self.console.print(table)

    def cmd_history_chat(self, args: str):
        target_sid = args.strip() or self.session_id
        messages = self.history_db.get_messages(target_sid)
        if not messages:
            self.console.print(f"[bright_black]No chat messages found for session: {target_sid}[/bright_black]")
            return

        table = Table(title=f"SQLite Chat Turns :: {target_sid}", border_style="bright_black", show_lines=True)
        table.add_column("Role", style="bold cyan", width=12)
        table.add_column("Content / Tool Trace", style="white")

        for m in messages:
            if m.role == "tool":
                detail = f"[cyan]Tool: {m.tool_name}[/cyan]\nOutput: {m.content}"
            elif m.role == "assistant" and not m.content and m.tool_name:
                detail = f"[cyan]Invoked: {m.tool_name}[/cyan]\nArguments: {m.tool_arguments}"
            else:
                detail = m.content or ""
            table.add_row(m.role.upper(), detail)
        self.console.print(table)

    def cmd_clear_history(self):
        self.history_db.clear_history()
        self.console.print("[green][OK][/green] SQLite chat history and commands database purged.")

    def cmd_memory(self):
        stats = self.telemetry.sample()
        temp_dir = self.engine.temp_directory
        temp_size_mb = 0.0
        if os.path.exists(temp_dir):
            total_bytes = sum(os.path.getsize(os.path.join(temp_dir, f)) for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f)))
            temp_size_mb = total_bytes / (1024 * 1024)

        table = Table(title="System & Memory Telemetry", border_style="bright_black")
        table.add_column("Parameter", style="bold white")
        table.add_column("Metric Value", style="cyan")

        table.add_row("Process Resident Set Size (RSS)", f"{stats.get('rss_mb', 0.0):.2f} MB")
        table.add_row("Virtual Memory Size (VMS)", f"{stats.get('vms_mb', 0.0):.2f} MB")
        table.add_row("CPU Utilization", f"{stats.get('cpu_percent', 0.0):.1f} %")
        table.add_row("DuckDB Memory Ceiling", self.memory_limit)
        table.add_row("DuckDB Temp Disk Directory", temp_dir)
        table.add_row("Temp Spill Footprint", f"{temp_size_mb:.2f} MB")
        self.console.print(table)

    def cmd_artifacts(self, args: str):
        limit = int(args.strip()) if args.strip().isdigit() else 20
        artifacts = self.history_db.list_artifacts(limit=limit)
        if not artifacts:
            self.console.print("[bright_black]No recorded artifacts in SQLite storage.[/bright_black]")
            return

        table = Table(title=f"Persisted Artifacts in SQLite (Last {len(artifacts)})", border_style="bright_black", show_lines=True)
        table.add_column("#", style="bright_black", width=4)
        table.add_column("Created", style="bright_black", width=19)
        table.add_column("Path", style="bold cyan", overflow="fold")
        table.add_column("Rows", style="white", justify="right")
        table.add_column("Size", style="white", justify="right")

        for art in artifacts:
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(art["created_at"]))
            rows_str = f"{art['row_count']:,}" if art["row_count"] is not None else "-"
            size_str = f"{art['file_size_bytes'] / (1024 * 1024):.2f} MB" if art["file_size_bytes"] is not None else "-"
            table.add_row(str(art["id"]), time_str, art["artifact_path"], rows_str, size_str)
        self.console.print(table)

    def cmd_config(self, args: str):
        parts = args.strip().split(maxsplit=1)
        if not parts or not parts[0]:
            table = Table(title="Active Runtime Configuration", border_style="bright_black")
            table.add_column("Setting", style="bold white")
            table.add_column("Current Value", style="cyan")
            table.add_row("Model Name", self.model_name)
            table.add_row("Base URL", self._censor_secret(self.base_url))
            table.add_row("API Key", self._censor_secret(self.api_key))
            table.add_row("Memory Limit", self.memory_limit)
            table.add_row("Temp Directory", self.engine.temp_directory)
            table.add_row("SQLite Storage", self.history_db.db_path)
            self.console.print(table)
            self.console.print("[bright_black]Usage to update: /config <model|base_url|api_key|memory_limit|delete> [value][/bright_black]")
            return

        key = parts[0].lower()
        val = parts[1].strip() if len(parts) > 1 else ""

        if key in ("base_url", "url"):
            if not val:
                import getpass
                try:
                    val = getpass.getpass("Enter Base URL (censored): ").strip()
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[yellow]Canceled input.[/yellow]")
                    return
            if not val:
                self.console.print("[red][ERROR][/red] Base URL cannot be empty.")
                return
            self.base_url = val
            self.history_db.set_config("base_url", val)
            self.console.print("[green][OK][/green] Base URL set and saved to SQLite: [bright_black]****** (censored)[/bright_black]")

        elif key in ("api_key", "key"):
            if not val:
                import getpass
                try:
                    val = getpass.getpass("Enter API Key (censored): ").strip()
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[yellow]Canceled input.[/yellow]")
                    return
            if not val:
                self.console.print("[red][ERROR][/red] API key cannot be empty.")
                return
            self.api_key = val
            self.history_db.set_config("api_key", val)
            self.console.print("[green][OK][/green] API Key set and saved to SQLite: [bright_black]****** (censored)[/bright_black]")

        elif key in ("model", "model_name"):
            if not val:
                self.console.print("[red][ERROR][/red] Value required for model")
                return
            self.model_name = val
            self.history_db.set_config("model_name", val)
            self.console.print(f"[green][OK][/green] Model set and saved to SQLite: [cyan]{self.model_name}[/cyan]")

        elif key in ("memory", "memory_limit", "max_memory"):
            if not val:
                self.console.print("[red][ERROR][/red] Value required for memory_limit")
                return
            self.memory_limit = val
            self.engine.memory_limit = val
            self.engine._conn.execute(f"SET max_memory = '{self.memory_limit}';")
            self.history_db.set_config("memory_limit", val)
            self.console.print(f"[green][OK][/green] Engine memory limit set and saved to SQLite: [cyan]{self.memory_limit}[/cyan]")

        elif key in ("delete", "remove", "unset"):
            if not val:
                self.console.print("[red][ERROR][/red] Key name required to delete from SQLite config")
                return
            self.history_db.delete_config(val)
            self.console.print(f"[green][OK][/green] Removed configuration key '{val}' from SQLite.")

        else:
            self.console.print(f"[red][ERROR][/red] Unknown config setting '{key}'. Valid options: model, base_url, api_key, memory_limit, delete")

    def run(self):
        """Main REPL loop."""
        self._running = True
        self.print_banner()

        while self._running:
            try:
                rss = self._get_rss_mb()
                prompt_str = f"hexanna [{rss:.0f}MB]> "
                user_input = input(prompt_str).strip()
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[bright_black]Received shutdown signal. Exiting Hexanna IIVX.[/bright_black]")
                break

            if not user_input:
                continue

            # Scrub credentials from history buffer immediately if present
            if any(k in user_input.lower() for k in ("base_url", "api_key", "llm_api_key")):
                self._scrub_sensitive_history()

            # Record in SQLite history database (sanitized)
            self.history_db.add_command(self._sanitize_message(user_input), session_id=self.session_id)

            # Command routing
            lower = user_input.lower()
            if lower in ("/exit", "/quit", "exit", "quit"):
                self.console.print("[bright_black]Exiting Hexanna IIVX REPL.[/bright_black]")
                break
            elif lower == "/help":
                self.cmd_help()
            elif lower == "/clear":
                self.console.clear()
                self.print_banner()
            elif lower in ("/memory", "/stats"):
                self.cmd_memory()
            elif lower.startswith("/sessions"):
                self.cmd_sessions(user_input[len("/sessions"):])
            elif lower.startswith("/history-chat"):
                self.cmd_history_chat(user_input[len("/history-chat"):])
            elif lower.startswith("/history"):
                self.cmd_history(user_input[len("/history"):])
            elif lower == "/clear-history":
                self.cmd_clear_history()
            elif lower.startswith("/artifacts"):
                self.cmd_artifacts(user_input[len("/artifacts"):])
            elif lower.startswith("/inspect"):
                self.cmd_inspect(user_input[len("/inspect"):])
            elif lower.startswith("/profile"):
                self.cmd_profile(user_input[len("/profile"):])
            elif lower.startswith("/sql"):
                self.cmd_sql(user_input[len("/sql"):])
            elif lower.startswith("/run"):
                self.cmd_run(user_input[len("/run"):])
            elif lower.startswith("/config"):
                self.cmd_config(user_input[len("/config"):])
            elif any(user_input.upper().startswith(sql_word) for sql_word in ("SELECT", "WITH", "DESCRIBE", "EXPLAIN", "SHOW", "PRAGMA")):
                self.cmd_sql(user_input)
            else:
                # Default natural language query routed to autonomous agent
                self.console.print(f"[bright_black]Dispatching objective to agent harness:[/bright_black] {user_input}")
                self.cmd_run(user_input)

        self.engine.close()
        self.history_db.close()
        self._save_history()
