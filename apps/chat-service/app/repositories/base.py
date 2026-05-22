"""
Abstract repository interfaces.
"""

from abc import ABC, abstractmethod

from app.domain.models import Conversation, Message


class ConversationRepository(ABC):
    """
    Abstract interface for conversation persistence.

    Future implementations will map to PostgreSQL.
    """

    @abstractmethod
    async def get_all(self) -> list[Conversation]:
        """Retrieve all conversations, ordered by updated_at descending."""
        pass

    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Retrieve a specific conversation with all its messages."""
        pass

    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        pass

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation:
        """Update a conversation (e.g., title or updated_at)."""
        pass

    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    async def add_message(self, conversation_id: str, message: Message) -> Message:
        """Add a message to a conversation."""
        pass
