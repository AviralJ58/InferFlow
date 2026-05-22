"""
PostgreSQL implementation of the conversation repository.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Conversation, Message
from app.repositories.base import ConversationRepository
from app.db.models import ConversationModel, MessageModel


class PostgresConversationRepository(ConversationRepository):
    """PostgreSQL-backed repository for conversations and messages."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain_message(self, model: MessageModel) -> Message:
        return Message(
            id=str(model.id),
            role=model.role,
            content=model.content,
            created_at=model.created_at,
            metadata=model.metadata_ or {}
        )

    def _to_domain_conversation(self, model: ConversationModel) -> Conversation:
        return Conversation(
            id=str(model.id),
            title=model.title,
            messages=[self._to_domain_message(m) for m in model.messages] if model.messages else [],
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_all(self) -> list[Conversation]:
        stmt = select(ConversationModel).options(selectinload(ConversationModel.messages)).order_by(ConversationModel.updated_at.desc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain_conversation(m) for m in models]

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        stmt = select(ConversationModel).options(selectinload(ConversationModel.messages)).where(ConversationModel.id == conversation_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_domain_conversation(model)

    async def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        self._session.add(model)
        
        for msg in conversation.messages:
            msg_model = MessageModel(
                id=msg.id,
                conversation_id=conversation.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                metadata_=msg.metadata
            )
            self._session.add(msg_model)

        await self._session.commit()
        return conversation

    async def update(self, conversation: Conversation) -> Conversation:
        # Fetch the existing model
        stmt = select(ConversationModel).options(selectinload(ConversationModel.messages)).where(ConversationModel.id == conversation.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            # If not found, create it (upsert behavior)
            return await self.create(conversation)

        # Update fields
        model.title = conversation.title
        model.updated_at = conversation.updated_at

        # We will handle message appends explicitly, or we can just reconcile them here.
        # For a chat app, usually we just append messages. We will look at what's in memory vs DB.
        existing_msg_ids = {str(m.id) for m in model.messages}
        for msg in conversation.messages:
            if msg.id not in existing_msg_ids:
                new_msg = MessageModel(
                    id=msg.id,
                    conversation_id=conversation.id,
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at,
                    metadata_=msg.metadata
                )
                self._session.add(new_msg)
            else:
                # Update content if it's streaming and got updated
                for existing_msg in model.messages:
                    if str(existing_msg.id) == msg.id:
                        existing_msg.content = msg.content
                        existing_msg.metadata_ = msg.metadata
                        break

        await self._session.commit()
        return conversation

    async def delete(self, conversation_id: str) -> bool:
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True

    async def add_message(self, conversation_id: str, message: Message) -> Message:
        msg_model = MessageModel(
            id=message.id,
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
            metadata_=message.metadata
        )
        self._session.add(msg_model)
        
        # Update conversation's updated_at
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self._session.execute(stmt)
        conv_model = result.scalar_one_or_none()
        if conv_model:
            conv_model.updated_at = message.created_at
            
        await self._session.commit()
        return message
