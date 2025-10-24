import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import Message


class ConversationSession:
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        messages: Optional[List[Message]] = None,
    ):
        self.conversation_id = conversation_id
        self.messages = messages or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str) -> None:
        # Add a message to the conversation
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_messages(self) -> List[Message]:
        # Get all messages in the conversation
        return self.messages

    def clear(self) -> None:
        # Clear all messages
        self.messages = []
        self.conversation_id = None
        self.updated_at = datetime.now()

    def set_conversation_id(self, conversation_id: str) -> None:
        # Set the conversation ID
        self.conversation_id = conversation_id
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        # Convert session to dictionary for serialization
        return {
            "conversation_id": self.conversation_id,
            "messages": [m.model_dump() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        # Create session from dictionary
        messages = [Message(**m) for m in data.get("messages", [])]
        session = cls(
            conversation_id=data.get("conversation_id"),
            messages=messages,
        )

        if "created_at" in data:
            session.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            session.updated_at = datetime.fromisoformat(data["updated_at"])

        return session


class SessionManager:
    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            storage_dir = Path.home() / ".jarvis-cli" / "conversations"

        self.storage_dir = storage_dir
        self.current_session: Optional[ConversationSession] = None

    def _ensure_storage_dir(self) -> None:
        # Create storage directory if it doesn't exist
        if not self.storage_dir.exists():
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, conversation_id: str) -> Path:
        # Get path for a conversation session file
        return self.storage_dir / f"{conversation_id}.json"

    def new_session(self) -> ConversationSession:
        # Create a new conversation session
        self.current_session = ConversationSession()
        return self.current_session

    def get_current_session(self) -> Optional[ConversationSession]:
        # Get the current active session
        return self.current_session

    def save_session(self, session: ConversationSession) -> None:
        # Save conversation session to disk
        if not session.conversation_id:
            return  # Don't save sessions without conversation_id

        self._ensure_storage_dir()

        session_path = self._get_session_path(session.conversation_id)

        try:
            with open(session_path, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save session: {e}")

    def load_session(self, conversation_id: str) -> ConversationSession:
        # Load conversation session from disk
        session_path = self._get_session_path(conversation_id)

        if not session_path.exists():
            raise FileNotFoundError(f"Session not found: {conversation_id}")

        try:
            with open(session_path, "r") as f:
                data = json.load(f)
            session = ConversationSession.from_dict(data)
            self.current_session = session
            return session
        except Exception as e:
            raise RuntimeError(f"Failed to load session: {e}")

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        # List recent conversation sessions
        self._ensure_storage_dir()

        sessions = []

        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                sessions.append({
                    "conversation_id": data.get("conversation_id"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "message_count": len(data.get("messages", [])),
                })
            except Exception:
                continue

        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return sessions[:limit]

    def delete_session(self, conversation_id: str) -> None:
        # Delete a conversation session from disk
        session_path = self._get_session_path(conversation_id)

        if session_path.exists():
            session_path.unlink()

        # Clear current session if it's the one being deleted
        if self.current_session and self.current_session.conversation_id == conversation_id:
            self.current_session = None

    def auto_save_current(self) -> None:
        # Auto-save the current session if it has a conversation_id
        if self.current_session and self.current_session.conversation_id:
            self.save_session(self.current_session)
