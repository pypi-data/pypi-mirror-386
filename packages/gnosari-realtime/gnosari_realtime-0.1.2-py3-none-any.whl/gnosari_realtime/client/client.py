"""Realtime WebSocket client implementation."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..core.schemas import Message, MessageType, SubscriptionMessage, PublishMessage


logger = logging.getLogger(__name__)


class RealtimeClient:
    """Python SDK client for connecting to Gnosari Realtime server."""
    
    def __init__(
        self,
        url: str,
        auth_token: Optional[str] = None,
        reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
    ):
        self.url = url
        self.auth_token = auth_token
        self.reconnect = reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        self._websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._connected = False
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._pending_messages: List[Dict[str, Any]] = []
        self._reconnect_attempts = 0
        self._should_reconnect = True
        
        self._connection_task: Optional[asyncio.Task] = None
        self._message_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """Connect to the WebSocket server."""
        if self._connected:
            return
        
        try:
            extra_headers = {}
            if self.auth_token:
                extra_headers["Authorization"] = f"Bearer {self.auth_token}"
            
            self._websocket = await websockets.connect(
                self.url,
                extra_headers=extra_headers,
                ping_interval=30,
                ping_timeout=10,
            )
            
            self._connected = True
            self._reconnect_attempts = 0
            logger.info(f"Connected to {self.url}")
            
            self._message_task = asyncio.create_task(self._message_listener())
            
            await self._send_pending_messages()
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.url}: {e}")
            if self.reconnect and self._should_reconnect:
                await self._attempt_reconnect()
            else:
                raise
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        self._should_reconnect = False
        
        if self._message_task:
            self._message_task.cancel()
        
        if self._websocket:
            await self._websocket.close()
        
        self._connected = False
        logger.info("Disconnected from server")
    
    async def subscribe(
        self,
        channel: str,
        callback: Callable[[Dict[str, Any]], None],
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Subscribe to a channel with a callback function."""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = []
        
        self._subscriptions[channel].append(callback)
        
        message = SubscriptionMessage(
            payload={
                "channel": channel,
                "filters": filters or {}
            }
        )
        
        await self._send_message(message.model_dump())
    
    async def unsubscribe(self, channel: str, callback: Optional[Callable] = None) -> None:
        """Unsubscribe from a channel."""
        if channel not in self._subscriptions:
            return
        
        if callback:
            try:
                self._subscriptions[channel].remove(callback)
            except ValueError:
                pass
            
            if not self._subscriptions[channel]:
                del self._subscriptions[channel]
        else:
            del self._subscriptions[channel]
        
        message = Message(
            type=MessageType.COMMAND,
            action="unsubscribe",
            payload={"channel": channel}
        )
        
        await self._send_message(message.model_dump())
    
    async def publish(self, channel: str, data: Any) -> None:
        """Publish data to a channel."""
        message = PublishMessage(
            payload={
                "channel": channel,
                "data": data
            }
        )
        
        await self._send_message(message.model_dump())
    
    async def send_custom_message(
        self,
        action: str,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.COMMAND,
    ) -> None:
        """Send a custom message to the server."""
        message = Message(
            type=message_type,
            action=action,
            payload=payload
        )
        
        await self._send_message(message.model_dump())
    
    def add_message_handler(self, action: str, handler: Callable[[Message], None]) -> None:
        """Add a handler for specific message actions."""
        if action not in self._message_handlers:
            self._message_handlers[action] = []
        
        self._message_handlers[action].append(handler)
    
    def remove_message_handler(self, action: str, handler: Callable[[Message], None]) -> bool:
        """Remove a message handler."""
        if action not in self._message_handlers:
            return False
        
        try:
            self._message_handlers[action].remove(handler)
            if not self._message_handlers[action]:
                del self._message_handlers[action]
            return True
        except ValueError:
            return False
    
    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._connected and self._websocket is not None
    
    async def ping(self) -> bool:
        """Send a ping message to test connectivity."""
        try:
            message = Message(
                type=MessageType.COMMAND,
                action="ping",
                payload={}
            )
            await self._send_message(message.model_dump())
            return True
        except Exception:
            return False
    
    async def _send_message(self, message_data: Dict[str, Any]) -> None:
        """Send a message to the WebSocket server."""
        if not self.is_connected:
            if self.reconnect:
                self._pending_messages.append(message_data)
                await self.connect()
            else:
                raise ConnectionError("Not connected to server")
        
        try:
            await self._websocket.send(json.dumps(message_data))
        except (ConnectionClosed, WebSocketException) as e:
            logger.error(f"Error sending message: {e}")
            self._connected = False
            if self.reconnect and self._should_reconnect:
                self._pending_messages.append(message_data)
                await self._attempt_reconnect()
            else:
                raise
    
    async def _message_listener(self) -> None:
        """Listen for incoming messages from the server."""
        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        
        except ConnectionClosed:
            logger.info("WebSocket connection closed")
            self._connected = False
            if self.reconnect and self._should_reconnect:
                await self._attempt_reconnect()
        
        except Exception as e:
            logger.error(f"Message listener error: {e}")
            self._connected = False
            if self.reconnect and self._should_reconnect:
                await self._attempt_reconnect()
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle incoming messages from the server."""
        try:
            message = Message(**data)
            
            await self._process_message_handlers(message)
            
            if message.action == "message" and "channel" in message.payload:
                await self._handle_channel_message(message)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_channel_message(self, message: Message) -> None:
        """Handle messages broadcast to subscribed channels."""
        channel = message.payload.get("channel")
        if not channel or channel not in self._subscriptions:
            return
        
        message_data = message.payload.get("data", {})
        
        for callback in self._subscriptions[channel]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message_data)
                else:
                    callback(message_data)
            except Exception as e:
                logger.error(f"Error in subscription callback for {channel}: {e}")
    
    async def _process_message_handlers(self, message: Message) -> None:
        """Process registered message handlers."""
        if message.action not in self._message_handlers:
            return
        
        for handler in self._message_handlers[message.action]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Error in message handler for {message.action}: {e}")
    
    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to the server."""
        if self._reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached")
            self._should_reconnect = False
            return
        
        self._reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self._reconnect_attempts - 1))  # Exponential backoff
        
        logger.info(f"Attempting to reconnect in {delay}s (attempt {self._reconnect_attempts}/{self.max_reconnect_attempts})")
        await asyncio.sleep(delay)
        
        try:
            await self.connect()
        except Exception as e:
            logger.error(f"Reconnect attempt {self._reconnect_attempts} failed: {e}")
            if self._reconnect_attempts < self.max_reconnect_attempts:
                await self._attempt_reconnect()
    
    async def _send_pending_messages(self) -> None:
        """Send any messages that were queued while disconnected."""
        if not self._pending_messages:
            return
        
        pending = self._pending_messages.copy()
        self._pending_messages.clear()
        
        for message_data in pending:
            try:
                await self._websocket.send(json.dumps(message_data))
            except Exception as e:
                logger.error(f"Failed to send pending message: {e}")
                self._pending_messages.append(message_data)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()