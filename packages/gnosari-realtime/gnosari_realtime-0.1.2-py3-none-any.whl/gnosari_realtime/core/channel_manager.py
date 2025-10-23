"""Channel management for pub/sub functionality."""

import asyncio
from typing import Dict, List, Set, Optional, Callable, Any
from uuid import uuid4

from .schemas import Message


class ChannelSubscription:
    """Represents a subscription to a channel."""
    
    def __init__(
        self,
        channel: str,
        connection_id: str,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(uuid4())
        self.channel = channel
        self.connection_id = connection_id
        self.user_id = user_id
        self.filters = filters or {}
        self.created_at = asyncio.get_event_loop().time()


class ChannelManager:
    """Manages channel subscriptions and message routing."""
    
    def __init__(self):
        self._subscriptions: Dict[str, Dict[str, ChannelSubscription]] = {}
        self._connection_channels: Dict[str, Set[str]] = {}
        self._message_handlers: Dict[str, List[Callable]] = {}
    
    async def subscribe(
        self,
        channel: str,
        connection_id: str,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> ChannelSubscription:
        """Subscribe a connection to a channel."""
        subscription = ChannelSubscription(channel, connection_id, user_id, filters)
        
        if channel not in self._subscriptions:
            self._subscriptions[channel] = {}
        
        self._subscriptions[channel][connection_id] = subscription
        
        if connection_id not in self._connection_channels:
            self._connection_channels[connection_id] = set()
        
        self._connection_channels[connection_id].add(channel)
        
        return subscription
    
    async def unsubscribe(self, channel: str, connection_id: str) -> bool:
        """Unsubscribe a connection from a channel."""
        if channel not in self._subscriptions:
            return False
        
        if connection_id not in self._subscriptions[channel]:
            return False
        
        del self._subscriptions[channel][connection_id]
        
        if connection_id in self._connection_channels:
            self._connection_channels[connection_id].discard(channel)
        
        if not self._subscriptions[channel]:
            del self._subscriptions[channel]
        
        return True
    
    async def unsubscribe_all(self, connection_id: str) -> List[str]:
        """Unsubscribe a connection from all channels."""
        if connection_id not in self._connection_channels:
            return []
        
        channels = list(self._connection_channels[connection_id])
        
        for channel in channels:
            await self.unsubscribe(channel, connection_id)
        
        if connection_id in self._connection_channels:
            del self._connection_channels[connection_id]
        
        return channels
    
    def get_subscriptions(self, channel: str) -> List[ChannelSubscription]:
        """Get all subscriptions for a channel."""
        if channel not in self._subscriptions:
            return []
        
        return list(self._subscriptions[channel].values())
    
    def get_connection_channels(self, connection_id: str) -> Set[str]:
        """Get all channels a connection is subscribed to."""
        return self._connection_channels.get(connection_id, set())
    
    def get_channel_count(self, channel: str) -> int:
        """Get the number of subscribers for a channel."""
        return len(self._subscriptions.get(channel, {}))
    
    def get_total_subscriptions(self) -> int:
        """Get the total number of active subscriptions."""
        return sum(len(subs) for subs in self._subscriptions.values())
    
    def get_active_channels(self) -> List[str]:
        """Get all active channels with at least one subscription."""
        return list(self._subscriptions.keys())
    
    def add_message_handler(self, channel: str, handler: Callable) -> None:
        """Add a message handler for a specific channel."""
        if channel not in self._message_handlers:
            self._message_handlers[channel] = []
        
        self._message_handlers[channel].append(handler)
    
    def remove_message_handler(self, channel: str, handler: Callable) -> bool:
        """Remove a message handler for a specific channel."""
        if channel not in self._message_handlers:
            return False
        
        try:
            self._message_handlers[channel].remove(handler)
            if not self._message_handlers[channel]:
                del self._message_handlers[channel]
            return True
        except ValueError:
            return False
    
    async def process_message_handlers(self, channel: str, message: Message) -> None:
        """Process all message handlers for a channel."""
        if channel not in self._message_handlers:
            return
        
        for handler in self._message_handlers[channel]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception:
                pass
    
    def _match_filters(
        self, subscription: ChannelSubscription, message: Message
    ) -> bool:
        """Check if a message matches subscription filters."""
        if not subscription.filters:
            return True
        
        for key, expected_value in subscription.filters.items():
            if key == "user_id":
                if message.metadata.user_id != expected_value:
                    return False
            elif key == "action":
                if message.action != expected_value:
                    return False
            elif key == "type":
                if message.type != expected_value:
                    return False
            elif key in message.payload:
                if message.payload[key] != expected_value:
                    return False
            else:
                return False
        
        return True