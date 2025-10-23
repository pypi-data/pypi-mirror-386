"""Repository implementations for data persistence."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Message, Connection, Subscription, db_manager
from ..core.schemas import Message as MessageSchema


class MessageRepository:
    """Repository for message persistence operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_message(self, message: MessageSchema, channel: str) -> Message:
        """Save a message to the database."""
        db_message = Message(
            message_id=message.id,
            channel=channel,
            message_type=message.type.value,
            action=message.action,
            version=message.version,
            payload=message.payload,
            message_metadata=message.metadata.model_dump() if message.metadata else None,
            user_id=message.metadata.user_id if message.metadata else None,
            session_id=message.metadata.session_id if message.metadata else None,
            team_id=message.metadata.team_id if message.metadata else None,
        )
        
        self.session.add(db_message)
        await self.session.commit()
        await self.session.refresh(db_message)
        
        return db_message
    
    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Get a message by its ID."""
        stmt = select(Message).where(Message.message_id == message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_channel_messages(
        self,
        channel: str,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> List[Message]:
        """Get messages for a specific channel."""
        stmt = select(Message).where(Message.channel == channel)
        
        if user_id:
            stmt = stmt.where(Message.user_id == user_id)
        
        if team_id:
            stmt = stmt.where(Message.team_id == team_id)
        
        stmt = stmt.order_by(desc(Message.created_at)).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_user_messages(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Message]:
        """Get messages for a specific user."""
        stmt = (
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def delete_old_messages(self, days: int = 30) -> int:
        """Delete messages older than specified days."""
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
        
        stmt = select(Message).where(Message.created_at < cutoff_date)
        result = await self.session.execute(stmt)
        messages_to_delete = result.scalars().all()
        
        for message in messages_to_delete:
            await self.session.delete(message)
        
        await self.session.commit()
        return len(messages_to_delete)


class ConnectionRepository:
    """Repository for connection tracking operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_connection(
        self,
        connection_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Connection:
        """Create a new connection record."""
        db_connection = Connection(
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id,
            connection_metadata=metadata,
        )
        
        self.session.add(db_connection)
        await self.session.commit()
        await self.session.refresh(db_connection)
        
        return db_connection
    
    async def update_connection_status(
        self,
        connection_id: str,
        status: str,
        disconnected_at: Optional[datetime] = None,
    ) -> bool:
        """Update connection status."""
        stmt = (
            update(Connection)
            .where(Connection.connection_id == connection_id)
            .values(
                status=status,
                disconnected_at=disconnected_at,
                updated_at=datetime.utcnow(),
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        stmt = select(Connection).where(Connection.connection_id == connection_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_connections(self, user_id: Optional[str] = None) -> List[Connection]:
        """Get all active connections, optionally filtered by user."""
        stmt = select(Connection).where(Connection.status == "active")
        
        if user_id:
            stmt = stmt.where(Connection.user_id == user_id)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def cleanup_old_connections(self, hours: int = 24) -> int:
        """Clean up old inactive connections."""
        cutoff_date = datetime.utcnow() - datetime.timedelta(hours=hours)
        
        stmt = select(Connection).where(
            and_(
                Connection.status != "active",
                Connection.updated_at < cutoff_date,
            )
        )
        
        result = await self.session.execute(stmt)
        connections_to_delete = result.scalars().all()
        
        for connection in connections_to_delete:
            await self.session.delete(connection)
        
        await self.session.commit()
        return len(connections_to_delete)


class SubscriptionRepository:
    """Repository for subscription tracking operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_subscription(
        self,
        subscription_id: str,
        connection_id: str,
        channel: str,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Subscription:
        """Create a new subscription record."""
        db_subscription = Subscription(
            subscription_id=subscription_id,
            connection_id=connection_id,
            channel=channel,
            user_id=user_id,
            filters=filters,
        )
        
        self.session.add(db_subscription)
        await self.session.commit()
        await self.session.refresh(db_subscription)
        
        return db_subscription
    
    async def end_subscription(self, subscription_id: str) -> bool:
        """Mark a subscription as ended."""
        stmt = (
            update(Subscription)
            .where(Subscription.subscription_id == subscription_id)
            .values(
                unsubscribed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def get_channel_subscriptions(self, channel: str) -> List[Subscription]:
        """Get all active subscriptions for a channel."""
        stmt = select(Subscription).where(
            and_(
                Subscription.channel == channel,
                Subscription.unsubscribed_at.is_(None),
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_connection_subscriptions(self, connection_id: str) -> List[Subscription]:
        """Get all active subscriptions for a connection."""
        stmt = select(Subscription).where(
            and_(
                Subscription.connection_id == connection_id,
                Subscription.unsubscribed_at.is_(None),
            )
        )
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def cleanup_old_subscriptions(self, days: int = 7) -> int:
        """Clean up old ended subscriptions."""
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
        
        stmt = select(Subscription).where(
            and_(
                Subscription.unsubscribed_at.is_not(None),
                Subscription.updated_at < cutoff_date,
            )
        )
        
        result = await self.session.execute(stmt)
        subscriptions_to_delete = result.scalars().all()
        
        for subscription in subscriptions_to_delete:
            await self.session.delete(subscription)
        
        await self.session.commit()
        return len(subscriptions_to_delete)


class RepositoryManager:
    """Manager for all repositories with session handling."""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def get_repositories(self) -> tuple[MessageRepository, ConnectionRepository, SubscriptionRepository]:
        """Get repository instances with a shared session."""
        session = self.db_manager.get_session()
        
        message_repo = MessageRepository(session)
        connection_repo = ConnectionRepository(session)
        subscription_repo = SubscriptionRepository(session)
        
        return message_repo, connection_repo, subscription_repo
    
    async def close_session(self, session: AsyncSession) -> None:
        """Close a database session."""
        await session.close()


# Global repository manager instance
repo_manager = RepositoryManager()