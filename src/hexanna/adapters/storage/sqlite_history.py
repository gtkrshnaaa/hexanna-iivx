import os
import time
import json
import sqlite3
from typing import List, Dict, Any, Optional
from hexanna.ports.chat_history import IChatHistoryRepository
from hexanna.domain.models import ChatMessage, ChatSession

DEFAULT_DB_PATH = os.path.expanduser("~/.hexanna_history.db")

class SQLiteChatHistory(IChatHistoryRepository):
    """Production-grade SQLite persistence adapter for Hexanna chat and execution history."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA synchronous = NORMAL;")

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                tool_call_id TEXT,
                tool_name TEXT,
                tool_arguments TEXT,
                tool_result TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                command_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'success',
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                artifact_path TEXT NOT NULL,
                file_size_bytes INTEGER,
                row_count INTEGER,
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_commands_created_at ON commands(created_at);
            CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id);
        """)
        self._conn.commit()

    def create_session(self, session_id: str, title: str) -> ChatSession:
        now = time.time()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO sessions (session_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    title = excluded.title,
                    updated_at = excluded.updated_at
                """,
                (session_id, title, now, now)
            )
        return ChatSession(session_id=session_id, title=title, created_at=now, updated_at=now, message_count=0)

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        cursor = self._conn.cursor()
        row = cursor.execute(
            """
            SELECT s.session_id, s.title, s.created_at, s.updated_at, COUNT(m.id) as msg_count
            FROM sessions s
            LEFT JOIN messages m ON s.session_id = m.session_id
            WHERE s.session_id = ?
            GROUP BY s.session_id
            """,
            (session_id,)
        ).fetchone()

        if not row:
            return None
        return ChatSession(
            session_id=row["session_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            message_count=row["msg_count"]
        )

    def list_sessions(self, limit: int = 20) -> List[ChatSession]:
        cursor = self._conn.cursor()
        rows = cursor.execute(
            """
            SELECT s.session_id, s.title, s.created_at, s.updated_at, COUNT(m.id) as msg_count
            FROM sessions s
            LEFT JOIN messages m ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        return [
            ChatSession(
                session_id=r["session_id"],
                title=r["title"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                message_count=r["msg_count"]
            )
            for r in rows
        ]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_arguments: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Dict[str, Any]] = None
    ) -> int:
        now = time.time()
        args_json = json.dumps(tool_arguments) if tool_arguments is not None else None
        res_json = json.dumps(tool_result) if tool_result is not None else None

        with self._conn:
            # Ensure session exists
            self._conn.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, f"Session {session_id}", now, now)
            )
            # Update session timestamp
            self._conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id)
            )
            cursor = self._conn.execute(
                """
                INSERT INTO messages (
                    session_id, role, content, tool_call_id, tool_name,
                    tool_arguments, tool_result, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content, tool_call_id, tool_name, args_json, res_json, now)
            )
            return cursor.lastrowid

    def get_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        cursor = self._conn.cursor()
        rows = cursor.execute(
            """
            SELECT role, content, tool_call_id, tool_name, tool_arguments, tool_result, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (session_id, limit)
        ).fetchall()

        messages = []
        for r in rows:
            args = json.loads(r["tool_arguments"]) if r["tool_arguments"] else None
            res = json.loads(r["tool_result"]) if r["tool_result"] else None
            messages.append(
                ChatMessage(
                    role=r["role"],
                    content=r["content"],
                    tool_call_id=r["tool_call_id"],
                    tool_name=r["tool_name"],
                    tool_arguments=args,
                    tool_result=res,
                    timestamp=r["created_at"]
                )
            )
        return messages

    def add_command(
        self,
        command_text: str,
        session_id: Optional[str] = None,
        status: str = "success"
    ) -> int:
        now = time.time()
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO commands (session_id, command_text, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, command_text, status, now)
            )
            return cursor.lastrowid

    def list_commands(self, limit: int = 20) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        rows = cursor.execute(
            """
            SELECT id, session_id, command_text, status, created_at
            FROM commands
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "command_text": r["command_text"],
                "status": r["status"],
                "created_at": r["created_at"]
            }
            for r in rows
        ]

    def set_config(self, key: str, value: str) -> None:
        now = time.time()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (key, value, now)
            )

    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        cursor = self._conn.cursor()
        row = cursor.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        if row:
            return row["value"]
        return default

    def get_all_config(self) -> Dict[str, str]:
        cursor = self._conn.cursor()
        rows = cursor.execute("SELECT key, value FROM config").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def delete_config(self, key: str) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM config WHERE key = ?", (key,))

    def record_artifact(
        self,
        session_id: str,
        artifact_path: str,
        file_size_bytes: Optional[int] = None,
        row_count: Optional[int] = None
    ) -> int:
        now = time.time()
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO artifacts (session_id, artifact_path, file_size_bytes, row_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, artifact_path, file_size_bytes, row_count, now)
            )
            return cursor.lastrowid

    def list_artifacts(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        if session_id:
            rows = cursor.execute(
                """
                SELECT id, session_id, artifact_path, file_size_bytes, row_count, created_at
                FROM artifacts
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit)
            ).fetchall()
        else:
            rows = cursor.execute(
                """
                SELECT id, session_id, artifact_path, file_size_bytes, row_count, created_at
                FROM artifacts
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "artifact_path": r["artifact_path"],
                "file_size_bytes": r["file_size_bytes"],
                "row_count": r["row_count"],
                "created_at": r["created_at"]
            }
            for r in rows
        ]

    def clear_history(self) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM messages;")
            self._conn.execute("DELETE FROM commands;")
            self._conn.execute("DELETE FROM sessions;")
            self._conn.execute("DELETE FROM artifacts;")
        self._conn.execute("VACUUM;")

    def close(self) -> None:
        if self._conn:
            self._conn.close()
