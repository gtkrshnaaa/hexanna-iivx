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
    def close(self) -> None:
        """Close storage resources."""
        pass
