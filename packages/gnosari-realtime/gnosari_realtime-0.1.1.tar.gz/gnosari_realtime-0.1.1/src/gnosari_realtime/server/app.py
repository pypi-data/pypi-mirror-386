"""Main Starlette application."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from starlette.applications import Starlette
from starlette.authentication import requires
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..core.channel_manager import ChannelManager
from ..core.schemas import Message, MessageType
from ..infrastructure.database import db_manager
from ..infrastructure.redis_client import redis_manager
from ..infrastructure.opensearch_client import opensearch_manager
from .auth import auth_service, AuthenticatedUser
from .config import settings
from .connection_manager import ConnectionManager


logger = logging.getLogger(__name__)


class RealtimeServer:
    """Main realtime server application."""
    
    def __init__(self):
        self.channel_manager = ChannelManager()
        self.connection_manager = ConnectionManager(self.channel_manager)
        self.app = self._create_app()
    
    async def startup(self) -> None:
        """Initialize services on startup."""
        logger.info("Starting Gnosari Realtime Server")
        
        try:
            await db_manager.create_tables()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
        
        try:
            await redis_manager.connect()
            logger.info("Redis connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
        
        try:
            await opensearch_manager.connect()
            logger.info("OpenSearch connected")
        except Exception as e:
            logger.error(f"OpenSearch connection failed: {e}")
    
    async def shutdown(self) -> None:
        """Cleanup services on shutdown."""
        logger.info("Shutting down Gnosari Realtime Server")
        
        try:
            await redis_manager.disconnect()
        except Exception as e:
            logger.error(f"Redis disconnect failed: {e}")
        
        try:
            await opensearch_manager.disconnect()
        except Exception as e:
            logger.error(f"OpenSearch disconnect failed: {e}")
        
        try:
            await db_manager.close()
        except Exception as e:
            logger.error(f"Database close failed: {e}")
    
    def _create_app(self) -> Starlette:
        """Create the Starlette application."""
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=["*"] if settings.debug else [],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
            Middleware(AuthenticationMiddleware, backend=auth_service.auth_backend),
        ]
        
        routes = [
            WebSocketRoute("/ws/v1", self._websocket_endpoint),
            Route("/health", self._health_check, methods=["GET"]),
            Route("/api/v1/channels", self._list_channels, methods=["GET"]),
            Route("/api/v1/publish/{channel}", self._publish_message, methods=["POST"]),
            Route("/api/v1/stats", self._get_stats, methods=["GET"]),
            Route("/api/v1/search", self._search_messages, methods=["GET"]),
            Route("/api/v1/analytics", self._get_analytics, methods=["GET"]),
            Route("/api/v1/auth/token", self._create_token, methods=["POST"]),
        ]
        
        app = Starlette(
            routes=routes,
            middleware=middleware,
            debug=settings.debug,
        )
        
        app.add_event_handler("startup", self.startup)
        app.add_event_handler("shutdown", self.shutdown)
        
        return app
    
    async def _websocket_endpoint(self, websocket: WebSocket) -> None:
        """Handle WebSocket connections."""
        try:
            user = await auth_service.authenticate_websocket(websocket)
            await websocket.accept()
            
            connection = await self.connection_manager.add_connection(
                websocket, 
                user.user_id if user else None
            )
            
            while True:
                message = await websocket.receive_text()
                await self.connection_manager.handle_message(connection, message)
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await websocket.close(code=1011)
            except:
                pass
        finally:
            if 'connection' in locals():
                await self.connection_manager.remove_connection(connection.id)
    
    async def _health_check(self, request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({
            "status": "healthy",
            "connections": self.connection_manager.get_active_connections_count(),
            "channels": len(self.channel_manager.get_active_channels()),
            "subscriptions": self.channel_manager.get_total_subscriptions()
        })
    
    async def _list_channels(self, request) -> JSONResponse:
        """List active channels."""
        channels = []
        for channel_name in self.channel_manager.get_active_channels():
            subscriber_count = self.channel_manager.get_channel_count(channel_name)
            channels.append({
                "name": channel_name,
                "subscribers": subscriber_count
            })
        
        return JSONResponse({"channels": channels})
    
    async def _publish_message(self, request: Request) -> JSONResponse:
        """Publish a message to a channel via HTTP API."""
        try:
            channel = request.path_params["channel"]
            body = await request.json()
            
            user = request.user if request.user.is_authenticated else None
            
            if not auth_service.can_user_publish(user, channel):
                return JSONResponse({
                    "success": False,
                    "error": "Unauthorized to publish to this channel"
                }, status_code=403)
            
            message = Message(
                type=MessageType.EVENT,
                action="message",
                payload={
                    "channel": channel,
                    "data": body.get("data", {})
                },
                metadata={
                    "user_id": user.user_id if user else None,
                    "timestamp": datetime.utcnow(),
                }
            )
            
            sent_count = await self.connection_manager.broadcast_to_channel(channel, message)
            
            try:
                await redis_manager.publish_message(channel, message)
                await opensearch_manager.index_message(message, channel)
            except Exception as e:
                logger.error(f"Failed to publish/index message: {e}")
            
            return JSONResponse({
                "success": True,
                "channel": channel,
                "sent_count": sent_count,
                "message_id": message.id
            })
        
        except Exception as e:
            logger.error(f"Error publishing message to {channel}: {e}")
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    async def _get_stats(self, request: Request) -> JSONResponse:
        """Get server statistics."""
        return JSONResponse({
            "connections": {
                "active": self.connection_manager.get_active_connections_count(),
                "unique_users": self.connection_manager.get_user_count()
            },
            "channels": {
                "active": len(self.channel_manager.get_active_channels()),
                "total_subscriptions": self.channel_manager.get_total_subscriptions()
            }
        })
    
    async def _search_messages(self, request: Request) -> JSONResponse:
        """Search messages using OpenSearch."""
        try:
            query = request.query_params.get("q", "")
            channel = request.query_params.get("channel")
            user_id = request.query_params.get("user_id")
            team_id = request.query_params.get("team_id")
            message_type = request.query_params.get("type")
            size = int(request.query_params.get("size", 20))
            from_ = int(request.query_params.get("from", 0))
            
            user = request.user if request.user.is_authenticated else None
            
            if channel and not auth_service.can_user_subscribe(user, channel):
                return JSONResponse({
                    "success": False,
                    "error": "Unauthorized to search this channel"
                }, status_code=403)
            
            results = await opensearch_manager.search_messages(
                query=query,
                channel=channel,
                user_id=user_id,
                team_id=team_id,
                message_type=message_type,
                size=size,
                from_=from_,
            )
            
            return JSONResponse({
                "success": True,
                "results": results
            })
        
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    async def _get_analytics(self, request: Request) -> JSONResponse:
        """Get message analytics."""
        try:
            channel = request.query_params.get("channel")
            user_id = request.query_params.get("user_id")
            team_id = request.query_params.get("team_id")
            
            user = request.user if request.user.is_authenticated else None
            
            if channel and not auth_service.can_user_subscribe(user, channel):
                return JSONResponse({
                    "success": False,
                    "error": "Unauthorized to view analytics for this channel"
                }, status_code=403)
            
            analytics = await opensearch_manager.get_message_analytics(
                channel=channel,
                user_id=user_id,
                team_id=team_id,
            )
            
            return JSONResponse({
                "success": True,
                "analytics": analytics
            })
        
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    async def _create_token(self, request: Request) -> JSONResponse:
        """Create a JWT token for authentication."""
        try:
            body = await request.json()
            
            user_id = body.get("user_id")
            username = body.get("username")
            email = body.get("email")
            teams = body.get("teams", [])
            permissions = body.get("permissions", [])
            is_admin = body.get("is_admin", False)
            
            if not user_id:
                return JSONResponse({
                    "success": False,
                    "error": "user_id is required"
                }, status_code=400)
            
            token = auth_service.create_user_token(
                user_id=user_id,
                username=username,
                email=email,
                teams=teams,
                permissions=permissions,
                is_admin=is_admin,
            )
            
            return JSONResponse({
                "success": True,
                "token": token,
                "user_id": user_id
            })
        
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            return JSONResponse({
                "success": False,
                "error": str(e)
            }, status_code=500)


def create_app() -> Starlette:
    """Create and return the Starlette application."""
    server = RealtimeServer()
    return server.app