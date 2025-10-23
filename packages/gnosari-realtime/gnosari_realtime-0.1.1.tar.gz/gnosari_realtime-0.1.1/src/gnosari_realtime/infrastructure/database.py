"""Database configuration and models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Index, JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr

from ..server.config import settings


class Base(DeclarativeBase):
    """Base model class."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Message(Base):
    """Message persistence model."""
    
    __tablename__ = "messages"
    
    message_id = Column(String(36), unique=True, nullable=False, index=True)
    channel = Column(String(100), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)
    action = Column(String(50), nullable=False)
    version = Column(String(10), nullable=False, default="v1")
    payload = Column(JSON, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    user_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    team_id = Column(String(36), nullable=True, index=True)
    
    __table_args__ = (
        Index("ix_messages_channel_created", "channel", "created_at"),
        Index("ix_messages_user_created", "user_id", "created_at"),
        Index("ix_messages_team_created", "team_id", "created_at"),
    )


class Connection(Base):
    """Connection tracking model."""
    
    __tablename__ = "connections"
    
    connection_id = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="active")
    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    disconnected_at = Column(DateTime, nullable=True)
    connection_metadata = Column(JSON, nullable=True)


class Subscription(Base):
    """Channel subscription tracking model."""
    
    __tablename__ = "subscriptions"
    
    subscription_id = Column(String(36), unique=True, nullable=False, index=True)
    connection_id = Column(String(36), nullable=False, index=True)
    channel = Column(String(100), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    filters = Column(JSON, nullable=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    unsubscribed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_subscriptions_connection_channel", "connection_id", "channel"),
        Index("ix_subscriptions_channel_active", "channel", "unsubscribed_at"),
    )


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.debug,
            pool_size=10,
            max_overflow=20,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def close(self) -> None:
        """Close the database engine."""
        await self.engine.dispose()
    
    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self.async_session()


# Global database manager instance
db_manager = DatabaseManager()