import os
import sys
import json
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from hexanna.__main__ import build_parser, resolve_runtime_config, read_input_or_stdin
from hexanna.adapters.storage.sqlite_history import SQLiteChatHistory

def test_resolve_runtime_config_defaults(tmp_path):
    db_file = str(tmp_path / "test_cfg.db")
    db = SQLiteChatHistory(db_path=db_file)
    parser = build_parser()
    args = parser.parse_args(["run", "test objective"])

    cfg = resolve_runtime_config(args, db)
    assert cfg["model"] is not None
    assert cfg["max_memory"] == "2GB"
    db.close()

def test_resolve_runtime_config_cli_overrides(tmp_path):
    db_file = str(tmp_path / "test_cfg.db")
    db = SQLiteChatHistory(db_path=db_file)
    db.set_config("model_name", "saved-model")
    db.set_config("memory_limit", "1GB")

    parser = build_parser()
    args = parser.parse_args(["run", "test", "--model", "custom-model", "--max-memory", "4GB"])

    cfg = resolve_runtime_config(args, db)
    assert cfg["model"] == "custom-model"
    assert cfg["max_memory"] == "4GB"
    db.close()

def test_read_input_or_stdin_positional():
    assert read_input_or_stdin("hello world", "test") == "hello world"

def test_read_input_or_stdin_from_pipe():
    with patch("sys.stdin", StringIO("piped objective content\n")):
        res = read_input_or_stdin("-", "objective")
        assert res == "piped objective content"

def test_read_input_or_stdin_empty_raises_exit():
    with patch("sys.stdin", StringIO("   \n")), patch("sys.stderr", StringIO()):
        with pytest.raises(SystemExit) as exc:
            read_input_or_stdin("-", "objective")
        assert exc.value.code == 2

def test_headless_query_execution(sample_parquet, tmp_path):
    out_file = str(tmp_path / "headless_out.parquet")
    parser = build_parser()
    args = parser.parse_args(["query", f"SELECT * FROM '{sample_parquet}' WHERE id < 10", out_file, "--json"])
    assert args.command == "query"
    assert args.output == out_file
    assert args.json is True

def test_headless_run_json_output(tmp_path, sample_parquet):
    parser = build_parser()
    args = parser.parse_args(["run", "Inspect dataset", "--json", "-q", "--max-iterations", "3"])
    assert args.command == "run"
    assert args.json is True
    assert args.quiet is True
    assert args.max_iterations == 3
