import pytest
from io import StringIO
from unittest.mock import patch
from rich.console import Console

from hexanna.tui.repl import HexannaCompleter, HexannaREPL

def test_hexanna_completer_commands():
    completer = HexannaCompleter()
    with patch("readline.get_line_buffer", return_value="/ins"), \
         patch("readline.get_begidx", return_value=0):
        match = completer.complete("/ins", 0)
        assert match == "/inspect"
        match2 = completer.complete("/ins", 1)
        assert match2 is None

def test_hexanna_completer_help():
    completer = HexannaCompleter()
    with patch("readline.get_line_buffer", return_value="/h"), \
         patch("readline.get_begidx", return_value=0):
        assert completer.complete("/h", 0) == "/help"

def test_repl_banner_and_help():
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.print_banner()
    output = string_io.getvalue()
    assert "HEXANNA IIVX" in output

    string_io.truncate(0)
    string_io.seek(0)
    repl.cmd_help()
    help_output = string_io.getvalue()
    assert "/inspect" in help_output
    assert "/sql" in help_output
    assert "/run" in help_output

def test_repl_cmd_inspect(sample_parquet):
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_inspect(sample_parquet)
    out = string_io.getvalue()
    assert "Dataset Overview" in out
    assert "Relational Schema" in out
    assert "username" in out

def test_repl_cmd_profile(sample_parquet):
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_profile(f"{sample_parquet} score")
    out = string_io.getvalue()
    assert "Statistical Sketches" in out
    assert "Non Null Count" in out

def test_repl_cmd_sql_preview(sample_parquet):
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_sql(f"SELECT username, count(*) as cnt FROM '{sample_parquet}' GROUP BY username")
    out = string_io.getvalue()
    assert "username" in out
    assert "cnt" in out

def test_repl_cmd_sql_stream_to_disk(sample_parquet, tmp_path):
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)
    out_file = str(tmp_path / "streamed.parquet")

    repl.cmd_sql(f"SELECT * FROM '{sample_parquet}' WHERE id < 50 -> {out_file}")
    out = string_io.getvalue()
    assert "Persisted" in out
    assert "streamed.parquet" in out

def test_repl_cmd_memory():
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_memory()
    out = string_io.getvalue()
    assert "System & Memory Telemetry" in out
    assert "Process Resident Set Size (RSS)" in out

def test_repl_cmd_config():
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_config("")
    out = string_io.getvalue()
    assert "Active Runtime Configuration" in out
    assert "llama-3.3-70b-versatile" in out

    repl.cmd_config("model custom-70b")
    assert repl.model_name == "custom-70b"

    repl.cmd_config("memory 4GB")
    assert repl.memory_limit == "4GB"
