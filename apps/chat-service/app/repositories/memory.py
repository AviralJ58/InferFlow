"""
In-memory implementation of the conversation repository.

Provides immediate state persistence for early development
before PostgreSQL is wired up.
"""

from datetime import UTC, datetime

from app.domain.models import Conversation, Message
from app.repositories.base import ConversationRepository


class InMemoryConversationRepository(ConversationRepository):
    """In-memory store for conversations and messages."""

    def __init__(self):
        # Maps conversation_id -> Conversation
        self._store: dict[str, Conversation] = {}

    async def get_all(self) -> list[Conversation]:
        """Get all conversations sorted by most recently updated."""
        conversations = list(self._store.values())
        return sorted(conversations, key=lambda c: c.updated_at, reverse=True)

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID."""
        return self._store.get(conversation_id)

    async def create(self, conversation: Conversation) -> Conversation:
        """Store a new conversation."""
        self._store[conversation.id] = conversation
        return conversation

    async def update(self, conversation: Conversation) -> Conversation:
        """Update conversation."""
        conversation.updated_at = datetime.now(UTC)
        self._store[conversation.id] = conversation
        return conversation

    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self._store:
            del self._store[conversation_id]
            return True
        return False

    async def add_message(self, conversation_id: str, message: Message) -> Message:
        """Add a message to a conversation."""
        if conversation_id not in self._store:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation = self._store[conversation_id]
        conversation.messages.append(message)
        conversation.updated_at = datetime.now(UTC)
        return message
