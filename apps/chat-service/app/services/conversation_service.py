"""
Service for managing conversations.
"""


from app.domain.models import Conversation
from app.repositories.base import ConversationRepository


class ConversationService:
    def __init__(self, repository: ConversationRepository):
        self._repository = repository

    async def get_all(self) -> list[Conversation]:
        """Get all conversations."""
        return await self._repository.get_all()

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID."""
        return await self._repository.get_by_id(conversation_id)

    async def create(self, title: str | None = None) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation()
        if title:
            conversation.title = title
        return await self._repository.create(conversation)

    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        return await self._repository.delete(conversation_id)
