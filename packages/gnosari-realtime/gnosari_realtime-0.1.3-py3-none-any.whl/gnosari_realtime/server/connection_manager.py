"""WebSocket connection management."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from uuid import uuid4

from starlette.websockets import WebSocket, WebSocketDisconnect

from ..core.channel_manager import ChannelManager
from ..core.schemas import Message, ErrorMessage, MessageType


logger = logging.getLogger(__name__)


class Connection:
    """Represents a WebSocket connection."""
    
    def __init__(self, websocket: WebSocket, user_id: Optional[str] = None):
        self.id = str(uuid4())
        self.websocket = websocket
        self.user_id = user_id
        self.connected_at = asyncio.get_event_loop().time()
        self.last_activity = self.connected_at
        self.is_alive = True
    
    async def send_message(self, message: Message) -> bool:
        """Send a message to the WebSocket connection."""
        try:
            await self.websocket.send_text(message.model_dump_json())
            self.last_activity = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            logger.error(f"Failed to send message to connection {self.id}: {e}")
            self.is_alive = False
            return False
    
    async def send_error(self, error_code: str, error_message: str, request_id: Optional[str] = None) -> bool:
        """Send an error message to the connection."""
        error_msg = ErrorMessage(
            id=request_id or str(uuid4()),
            payload={
                "code": error_code,
                "message": error_message,
                "retryable": False
            }
        )
        return await self.send_message(error_msg)
    
    async def close(self, code: int = 1000) -> None:
        """Close the WebSocket connection."""
        try:
            await self.websocket.close(code)
            self.is_alive = False
        except Exception as e:
            logger.error(f"Error closing connection {self.id}: {e}")


class ConnectionManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self, channel_manager: ChannelManager):
        self.channel_manager = channel_manager
        self._connections: Dict[str, Connection] = {}
        self._user_connections: Dict[str, Set[str]] = {}
        self._connection_lock = asyncio.Lock()
    
    async def add_connection(self, websocket: WebSocket, user_id: Optional[str] = None) -> Connection:
        """Add a new WebSocket connection."""
        connection = Connection(websocket, user_id)
        
        async with self._connection_lock:
            self._connections[connection.id] = connection
            
            if user_id:
                if user_id not in self._user_connections:
                    self._user_connections[user_id] = set()
                self._user_connections[user_id].add(connection.id)
        
        logger.info(f"New connection added: {connection.id} (user: {user_id})")
        return connection
    
    async def remove_connection(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._connection_lock:
            if connection_id not in self._connections:
                return
            
            connection = self._connections[connection_id]
            
            await self.channel_manager.unsubscribe_all(connection_id)
            
            if connection.user_id and connection.user_id in self._user_connections:
                self._user_connections[connection.user_id].discard(connection_id)
                if not self._user_connections[connection.user_id]:
                    del self._user_connections[connection.user_id]
            
            del self._connections[connection_id]
        
        logger.info(f"Connection removed: {connection_id}")
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        return self._connections.get(connection_id)
    
    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user."""
        if user_id not in self._user_connections:
            return []
        
        connections = []
        for conn_id in self._user_connections[user_id]:
            if conn_id in self._connections:
                connections.append(self._connections[conn_id])
        
        return connections
    
    async def broadcast_to_channel(self, channel: str, message: Message, exclude_connection: Optional[str] = None) -> int:
        """Broadcast a message to all subscribers of a channel."""
        subscriptions = self.channel_manager.get_subscriptions(channel)
        sent_count = 0
        
        for subscription in subscriptions:
            if exclude_connection and subscription.connection_id == exclude_connection:
                continue
            
            connection = self.get_connection(subscription.connection_id)
            if connection and connection.is_alive:
                success = await connection.send_message(message)
                if success:
                    sent_count += 1
                else:
                    await self.remove_connection(subscription.connection_id)
        
        return sent_count
    
    async def send_to_user(self, user_id: str, message: Message) -> int:
        """Send a message to all connections of a specific user."""
        connections = self.get_user_connections(user_id)
        sent_count = 0
        
        for connection in connections:
            if connection.is_alive:
                success = await connection.send_message(message)
                if success:
                    sent_count += 1
                else:
                    await self.remove_connection(connection.id)
        
        return sent_count
    
    def get_active_connections_count(self) -> int:
        """Get the total number of active connections."""
        return len(self._connections)
    
    def get_user_count(self) -> int:
        """Get the total number of unique users connected."""
        return len(self._user_connections)
    
    async def cleanup_dead_connections(self) -> int:
        """Remove dead connections and return count removed."""
        dead_connections = []
        
        for conn_id, connection in self._connections.items():
            if not connection.is_alive:
                dead_connections.append(conn_id)
        
        for conn_id in dead_connections:
            await self.remove_connection(conn_id)
        
        return len(dead_connections)
    
    async def handle_message(self, connection: Connection, raw_message: str) -> None:
        """Handle an incoming message from a WebSocket connection."""
        try:
            data = json.loads(raw_message)
            message = Message(**data)
            
            connection.last_activity = asyncio.get_event_loop().time()
            
            if message.action == "subscribe":
                await self._handle_subscribe(connection, message)
            elif message.action == "unsubscribe":
                await self._handle_unsubscribe(connection, message)
            elif message.action == "publish":
                await self._handle_publish(connection, message)
            elif message.action == "ping":
                await self._handle_ping(connection, message)
            else:
                await self._handle_custom_message(connection, message)
        
        except json.JSONDecodeError:
            await connection.send_error("INVALID_JSON", "Invalid JSON format", None)
        except Exception as e:
            logger.error(f"Error handling message from {connection.id}: {e}")
            await connection.send_error("MESSAGE_ERROR", str(e), None)
    
    async def _handle_subscribe(self, connection: Connection, message: Message) -> None:
        """Handle subscription request."""
        try:
            channel = message.payload.get("channel")
            if not channel:
                await connection.send_error("MISSING_CHANNEL", "Channel is required", message.id)
                return
            
            filters = message.payload.get("filters", {})
            
            await self.channel_manager.subscribe(channel, connection.id, connection.user_id, filters)
            
            response = Message(
                id=str(uuid4()),
                type=MessageType.RESPONSE,
                action="subscribed",
                payload={"channel": channel, "status": "success"}
            )
            await connection.send_message(response)
            
        except Exception as e:
            await connection.send_error("SUBSCRIBE_ERROR", str(e), message.id)
    
    async def _handle_unsubscribe(self, connection: Connection, message: Message) -> None:
        """Handle unsubscription request."""
        try:
            channel = message.payload.get("channel")
            if not channel:
                await connection.send_error("MISSING_CHANNEL", "Channel is required", message.id)
                return
            
            success = await self.channel_manager.unsubscribe(channel, connection.id)
            
            response = Message(
                id=str(uuid4()),
                type=MessageType.RESPONSE,
                action="unsubscribed",
                payload={"channel": channel, "status": "success" if success else "not_subscribed"}
            )
            await connection.send_message(response)
            
        except Exception as e:
            await connection.send_error("UNSUBSCRIBE_ERROR", str(e), message.id)
    
    async def _handle_publish(self, connection: Connection, message: Message) -> None:
        """Handle publish request."""
        try:
            channel = message.payload.get("channel")
            data = message.payload.get("data")
            
            if not channel:
                await connection.send_error("MISSING_CHANNEL", "Channel is required", message.id)
                return
            
            if data is None:
                await connection.send_error("MISSING_DATA", "Data is required", message.id)
                return
            
            published_message = Message(
                id=str(uuid4()),
                type=MessageType.EVENT,
                action="message",
                payload={"channel": channel, "data": data},
                metadata=message.metadata
            )
            
            sent_count = await self.broadcast_to_channel(channel, published_message, connection.id)
            
            response = Message(
                id=str(uuid4()),
                type=MessageType.RESPONSE,
                action="published",
                payload={"channel": channel, "sent_count": sent_count}
            )
            await connection.send_message(response)
            
        except Exception as e:
            await connection.send_error("PUBLISH_ERROR", str(e), message.id)
    
    async def _handle_ping(self, connection: Connection, message: Message) -> None:
        """Handle ping request."""
        response = Message(
            id=str(uuid4()),
            type=MessageType.RESPONSE,
            action="pong",
            payload={"timestamp": asyncio.get_event_loop().time()}
        )
        await connection.send_message(response)
    
    async def _handle_custom_message(self, connection: Connection, message: Message) -> None:
        """Handle custom message types (extend this for AI integration)."""
        logger.debug(f"Received custom message: {message.action} from {connection.id}")
        
        await connection.send_error("UNKNOWN_ACTION", f"Unknown action: {message.action}", message.id)