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
    assert "/artifacts" in help_output

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
    assert "(censored)" in out
    # Raw default base URL must NOT be displayed
    assert "https://api.groq.com/openai/v1" not in out

    repl.cmd_config("model custom-70b")
    assert repl.model_name == "custom-70b"

    repl.cmd_config("memory 4GB")
    assert repl.memory_limit == "4GB"

def test_repl_credentials_censored():
    repl = HexannaREPL()
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    secret_url = "https://my-super-secret-endpoint.internal/v1"
    repl.cmd_config(f"base_url {secret_url}")
    out = string_io.getvalue()
    assert repl.base_url == secret_url
    assert secret_url not in out
    assert "(censored)" in out

    string_io.truncate(0)
    string_io.seek(0)
    secret_key = "sk-super-confidential-token-999"
    repl.cmd_config(f"api_key {secret_key}")
    out2 = string_io.getvalue()
    assert repl.api_key == secret_key
    assert secret_key not in out2
    assert "(censored)" in out2

    # Verify error message sanitization
    sanitized = repl._sanitize_message(f"Fatal error reaching {secret_url} with {secret_key}")
    assert secret_url not in sanitized
    assert secret_key not in sanitized
    assert "****** (censored)" in sanitized

def test_repl_sqlite_history_commands(tmp_path):
    db_file = str(tmp_path / "repl_test.db")
    repl = HexannaREPL(db_path=db_file)
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=120)

    # Record command in SQLite
    repl.history_db.add_command("/inspect data.parquet", session_id=repl.session_id)
    repl.cmd_history("10")
    out = string_io.getvalue()
    assert "SQLite Command History" in out
    assert "/inspect data.parquet" in out

    # Check sessions table
    string_io.truncate(0)
    string_io.seek(0)
    repl.cmd_sessions("10")
    sess_out = string_io.getvalue()
    assert "SQLite Chat Sessions" in sess_out
    assert repl.session_id in sess_out

    # Add message and check history-chat
    repl.history_db.add_message(repl.session_id, role="user", content="Test prompt in chat")
    string_io.truncate(0)
    string_io.seek(0)
    repl.cmd_history_chat(repl.session_id)
    chat_out = string_io.getvalue()
    assert "Test prompt in chat" in chat_out

    # Clear history
    string_io.truncate(0)
    string_io.seek(0)
    repl.cmd_clear_history()
    clear_out = string_io.getvalue()
    assert "purged" in clear_out
    assert len(repl.history_db.list_sessions()) == 0
    repl.history_db.close()

def test_repl_sqlite_config_persistence(tmp_path):
    db_file = str(tmp_path / "config_test.db")
    repl1 = HexannaREPL(db_path=db_file)
    string_io = StringIO()
    repl1.console = Console(file=string_io, no_color=True, width=120)

    secret_url = "https://custom-private-llm.corp.net/v1"
    secret_key = "sk-corp-super-secret-key-12345"

    repl1.cmd_config(f"base_url {secret_url}")
    repl1.cmd_config(f"api_key {secret_key}")
    repl1.cmd_config("model custom-llama-model")
    repl1.cmd_config("memory 6GB")

    # Verify censorship in output
    out = string_io.getvalue()
    assert secret_url not in out
    assert secret_key not in out
    assert "****** (censored)" in out

    # Verify saved in SQLite
    assert repl1.history_db.get_config("base_url") == secret_url
    assert repl1.history_db.get_config("api_key") == secret_key
    assert repl1.history_db.get_config("model_name") == "custom-llama-model"
    assert repl1.history_db.get_config("memory_limit") == "6GB"
    repl1.history_db.close()

    # Re-initialize new REPL instance without args, pointing to same SQLite DB
    repl2 = HexannaREPL(db_path=db_file)
    assert repl2.base_url == secret_url
    assert repl2.api_key == secret_key
    assert repl2.model_name == "custom-llama-model"
    assert repl2.memory_limit == "6GB"

    # Test deleting a key
    string_io2 = StringIO()
    repl2.console = Console(file=string_io2, no_color=True, width=120)
    repl2.cmd_config("delete api_key")
    del_out = string_io2.getvalue()
    assert "Removed configuration key 'api_key'" in del_out
    assert repl2.history_db.get_config("api_key") is None
    repl2.history_db.close()

def test_repl_artifacts_recording(tmp_path, sample_parquet):
    db_file = str(tmp_path / "artifacts_test.db")
    repl = HexannaREPL(db_path=db_file)
    string_io = StringIO()
    repl.console = Console(file=string_io, no_color=True, width=160)

    out_file = str(tmp_path / "saved_records.parquet")
    repl.cmd_sql(f"SELECT * FROM '{sample_parquet}' WHERE id < 30 -> {out_file}")

    # Verify recorded in SQLite
    artifacts = repl.history_db.list_artifacts()
    assert len(artifacts) == 1
    assert artifacts[0]["artifact_path"] == out_file
    assert artifacts[0]["row_count"] == 30

    # Verify /artifacts command outputs the table
    string_io.truncate(0)
    string_io.seek(0)
    repl.cmd_artifacts("10")
    art_out = string_io.getvalue()
    assert "Persisted Artifacts in SQLite" in art_out
    assert "saved_records.parquet" in art_out
    repl.history_db.close()
