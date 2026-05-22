"""
FastAPI dependencies for the chat service.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import async_session
from app.repositories.base import ConversationRepository
from app.repositories.postgres import PostgresConversationRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session."""
    async with async_session() as session:
        yield session


from fastapi import Depends

async def get_conversation_repository(
    session: AsyncSession = Depends(get_db)
) -> ConversationRepository:
    """Dependency that provides the PostgresConversationRepository."""
    return PostgresConversationRepository(session)
