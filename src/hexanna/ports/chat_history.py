from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from hexanna.domain.models import ChatMessage, ChatSession

class IChatHistoryRepository(ABC):
    """Abstract port for persisting and querying chat sessions, messages, and command history."""

    @abstractmethod
    def create_session(self, session_id: str, title: str) -> ChatSession:
        """Create or initialize a chat session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Fetch a session by ID."""
        pass

    @abstractmethod
    def list_sessions(self, limit: int = 20) -> List[ChatSession]:
        """List active and historical chat sessions."""
        pass

    @abstractmethod
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
        """Append a message turn to the session."""
        pass

    @abstractmethod
    def get_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """Retrieve message turns for a given session."""
        pass

    @abstractmethod
    def add_command(
        self,
        command_text: str,
        session_id: Optional[str] = None,
        status: str = "success"
    ) -> int:
        """Append an interactive command execution entry."""
        pass

    @abstractmethod
    def list_commands(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent command history."""
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """Purge all sessions and history entries."""
        pass

    @abstractmethod
    def set_config(self, key: str, value: str) -> None:
        """Persist a configuration key-value pair in SQLite."""
        pass

    @abstractmethod
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Fetch a persistent configuration value from SQLite."""
        pass

    @abstractmethod
    def get_all_config(self) -> Dict[str, str]:
        """Retrieve all persistent configuration key-value pairs from SQLite."""
        pass

    @abstractmethod
    def delete_config(self, key: str) -> None:
        """Remove a configuration key from SQLite."""
        pass

    @abstractmethod
    def record_artifact(
        self,
        session_id: str,
        artifact_path: str,
        file_size_bytes: Optional[int] = None,
        row_count: Optional[int] = None
    ) -> int:
        """Record an out-of-core dataset artifact created by the system."""
        pass

    @abstractmethod
    def list_artifacts(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List generated artifacts stored in SQLite."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close storage resources."""
        pass
