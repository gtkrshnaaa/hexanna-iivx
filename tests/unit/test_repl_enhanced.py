import os
import json
import pytest
from io import StringIO
from rich.console import Console

from hexanna.tui.repl import HexannaCompleter, HexannaREPL
from hexanna.adapters.storage.sqlite_history import SQLiteChatHistory

def test_completer_includes_new_commands():
    completer = HexannaCompleter()
    assert "/models" in completer.COMMANDS
    assert "/model" in completer.COMMANDS
    assert "/export" in completer.COMMANDS
    assert "/tables" in completer.COMMANDS

def test_repl_cmd_models(tmp_path):
    db_file = str(tmp_path / "repl_test.db")
    repl = HexannaREPL(db_path=db_file)
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_models()
    out = string_io.getvalue()
    assert "Inference Models Catalog" in out
    assert "deepseek-flash" in out or "gemini-3.8-flash-high" in out
    assert "ACTIVE" in out
    repl.engine.close()
    repl.history_db.close()

def test_repl_cmd_model_switch(tmp_path):
    db_file = str(tmp_path / "repl_test.db")
    repl = HexannaREPL(db_path=db_file)
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_model("deepseek-flash")
    out = string_io.getvalue()
    assert "Active inference model switched to" in out
    assert repl.model_name == "deepseek-flash"

    # Verify saved to SQLite
    saved = repl.history_db.get_config("model_name")
    assert saved == "deepseek-flash"

    repl.engine.close()
    repl.history_db.close()

def test_repl_cmd_export_markdown(tmp_path):
    db_file = str(tmp_path / "repl_test.db")
    repl = HexannaREPL(db_path=db_file)
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    # Seed messages
    repl.history_db.add_message(repl.session_id, "user", "What is total revenue?")
    repl.history_db.add_message(repl.session_id, "assistant", "Total revenue is 45000.")

    export_file = str(tmp_path / "trace.md")
    repl.cmd_export(f"markdown {export_file}")
    out = string_io.getvalue()
    assert "Exported 2 turns to Markdown" in out
    assert os.path.exists(export_file)

    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "What is total revenue?" in content
    assert "Total revenue is 45000." in content

    repl.engine.close()
    repl.history_db.close()

def test_repl_cmd_export_json(tmp_path):
    db_file = str(tmp_path / "repl_test.db")
    repl = HexannaREPL(db_path=db_file)
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.history_db.add_message(repl.session_id, "user", "Inspect schema")
    export_json = str(tmp_path / "trace.json")
    repl.cmd_export(f"json {export_json}")

    assert os.path.exists(export_json)
    with open(export_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["session_id"] == repl.session_id
    assert len(data["messages"]) == 1

    repl.engine.close()
    repl.history_db.close()

def test_repl_cmd_tables(sample_parquet, tmp_path):
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    repl.cmd_tables(str(tmp_path))
    out = string_io.getvalue()
    assert "Discovered Tables & Datasets" in out
    assert "PARQUET" in out
    repl.engine.close()
    repl.history_db.close()
