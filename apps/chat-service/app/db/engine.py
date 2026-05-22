"""
SQLAlchemy engine and async session factory.
"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=20,
    max_overflow=10,
    echo=False,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
