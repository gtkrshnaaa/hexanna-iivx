import os
import pytest
from hexanna.adapters.storage.sqlite_history import SQLiteChatHistory

@pytest.fixture
def sqlite_db(tmp_path):
    db_file = str(tmp_path / "test_history.db")
    storage = SQLiteChatHistory(db_path=db_file)
    yield storage
    storage.close()

def test_sqlite_wal_mode(sqlite_db):
    cursor = sqlite_db._conn.cursor()
    mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
    assert mode.lower() == "wal"

def test_session_lifecycle(sqlite_db):
    session = sqlite_db.create_session("sess_1", "Analysis of TPC-H")
    assert session.session_id == "sess_1"
    assert session.title == "Analysis of TPC-H"

    fetched = sqlite_db.get_session("sess_1")
    assert fetched is not None
    assert fetched.session_id == "sess_1"
    assert fetched.message_count == 0

def test_add_and_get_messages(sqlite_db):
    session_id = "sess_2"
    sqlite_db.create_session(session_id, "Data pipeline run")

    msg_id1 = sqlite_db.add_message(
        session_id=session_id,
        role="user",
        content="Filter orders by price"
    )
    assert msg_id1 > 0

    msg_id2 = sqlite_db.add_message(
        session_id=session_id,
        role="tool",
        content='{"status": "success"}',
        tool_call_id="call_99",
        tool_name="execute_out_of_core_sql",
        tool_arguments={"query": "SELECT * FROM orders"},
        tool_result={"rows_written": 500}
    )
    assert msg_id2 > msg_id1

    messages = sqlite_db.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "Filter orders by price"
    assert messages[1].role == "tool"
    assert messages[1].tool_name == "execute_out_of_core_sql"
    assert messages[1].tool_arguments == {"query": "SELECT * FROM orders"}
    assert messages[1].tool_result == {"rows_written": 500}

def test_commands_history(sqlite_db):
    cmd_id1 = sqlite_db.add_command("/inspect data/orders.parquet", session_id="sess_3")
    cmd_id2 = sqlite_db.add_command("/sql SELECT count(*) FROM orders", session_id="sess_3")
    assert cmd_id2 > cmd_id1

    commands = sqlite_db.list_commands(limit=10)
    assert len(commands) == 2
    assert commands[0]["command_text"] == "/sql SELECT count(*) FROM orders"
    assert commands[1]["command_text"] == "/inspect data/orders.parquet"

def test_clear_history(sqlite_db):
    sqlite_db.create_session("sess_clear", "Temporary")
    sqlite_db.add_message("sess_clear", "user", "Hello")
    sqlite_db.add_command("test command", session_id="sess_clear")
    sqlite_db.record_artifact("sess_clear", "data/test.parquet", 100, 10)

    sqlite_db.clear_history()
    assert len(sqlite_db.list_sessions()) == 0
    assert len(sqlite_db.list_commands()) == 0
    assert len(sqlite_db.get_messages("sess_clear")) == 0
    assert len(sqlite_db.list_artifacts()) == 0

def test_sqlite_config_storage(sqlite_db):
    sqlite_db.set_config("base_url", "https://api.groq.com/openai/v1")
    sqlite_db.set_config("api_key", "sk-secret-token")
    sqlite_db.set_config("model_name", "llama-3.3-70b-versatile")

    assert sqlite_db.get_config("base_url") == "https://api.groq.com/openai/v1"
    assert sqlite_db.get_config("api_key") == "sk-secret-token"
    assert sqlite_db.get_config("model_name") == "llama-3.3-70b-versatile"
    assert sqlite_db.get_config("nonexistent", "fallback") == "fallback"

    all_cfg = sqlite_db.get_all_config()
    assert all_cfg["base_url"] == "https://api.groq.com/openai/v1"
    assert all_cfg["api_key"] == "sk-secret-token"

    # Upsert test
    sqlite_db.set_config("api_key", "sk-updated-token")
    assert sqlite_db.get_config("api_key") == "sk-updated-token"

    # Delete test
    sqlite_db.delete_config("api_key")
    assert sqlite_db.get_config("api_key") is None

def test_sqlite_artifacts_storage(sqlite_db):
    art_id1 = sqlite_db.record_artifact("sess_1", "output/result.parquet", 1048576, 50000)
    assert art_id1 > 0
    art_id2 = sqlite_db.record_artifact("sess_2", "output/summary.parquet", 2048, 10)
    assert art_id2 > art_id1

    all_arts = sqlite_db.list_artifacts()
    assert len(all_arts) == 2
    assert all_arts[0]["artifact_path"] == "output/summary.parquet"
    assert all_arts[1]["artifact_path"] == "output/result.parquet"

    sess1_arts = sqlite_db.list_artifacts(session_id="sess_1")
    assert len(sess1_arts) == 1
    assert sess1_arts[0]["artifact_path"] == "output/result.parquet"
    assert sess1_arts[0]["file_size_bytes"] == 1048576
    assert sess1_arts[0]["row_count"] == 50000
