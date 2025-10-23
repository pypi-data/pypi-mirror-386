"""Redis client for pub/sub and caching."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from ..core.schemas import Message
from ..server.config import settings


logger = logging.getLogger(__name__)


class RedisManager:
    """Manages Redis connections for pub/sub and caching."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[Redis] = None
        self._pubsub_redis: Optional[Redis] = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._pubsub_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
        
        if self._pubsub_redis is None:
            self._pubsub_redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        
        logger.info("Connected to Redis")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        for task in self._pubsub_tasks.values():
            task.cancel()
        
        self._pubsub_tasks.clear()
        
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        if self._pubsub_redis:
            await self._pubsub_redis.close()
            self._pubsub_redis = None
        
        logger.info("Disconnected from Redis")
    
    @property
    def redis(self) -> Redis:
        """Get the main Redis connection."""
        if self._redis is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis
    
    async def publish_message(self, channel: str, message: Message) -> int:
        """Publish a message to a Redis channel."""
        try:
            message_data = message.model_dump_json()
            return await self.redis.publish(f"channel:{channel}", message_data)
        except Exception as e:
            logger.error(f"Failed to publish message to Redis channel {channel}: {e}")
            return 0
    
    async def subscribe_to_channel(
        self,
        channel: str,
        callback: Callable[[Message], Any],
    ) -> None:
        """Subscribe to a Redis channel with a callback."""
        redis_channel = f"channel:{channel}"
        
        if channel not in self._subscribers:
            self._subscribers[channel] = []
            
            pubsub = self._pubsub_redis.pubsub()
            await pubsub.subscribe(redis_channel)
            
            self._pubsub_tasks[channel] = asyncio.create_task(
                self._handle_pubsub_messages(channel, pubsub)
            )
        
        self._subscribers[channel].append(callback)
        logger.debug(f"Subscribed to Redis channel: {channel}")
    
    async def unsubscribe_from_channel(
        self,
        channel: str,
        callback: Optional[Callable[[Message], Any]] = None,
    ) -> None:
        """Unsubscribe from a Redis channel."""
        if channel not in self._subscribers:
            return
        
        if callback:
            try:
                self._subscribers[channel].remove(callback)
            except ValueError:
                pass
        else:
            self._subscribers[channel].clear()
        
        if not self._subscribers[channel]:
            if channel in self._pubsub_tasks:
                self._pubsub_tasks[channel].cancel()
                del self._pubsub_tasks[channel]
            
            del self._subscribers[channel]
            logger.debug(f"Unsubscribed from Redis channel: {channel}")
    
    async def _handle_pubsub_messages(
        self,
        channel: str,
        pubsub,
    ) -> None:
        """Handle incoming pub/sub messages."""
        try:
            async for redis_message in pubsub.listen():
                if redis_message["type"] != "message":
                    continue
                
                try:
                    message_data = json.loads(redis_message["data"])
                    message = Message(**message_data)
                    
                    for callback in self._subscribers.get(channel, []):
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(message)
                            else:
                                callback(message)
                        except Exception as e:
                            logger.error(f"Error in Redis callback for {channel}: {e}")
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode Redis message: {e}")
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
        
        except asyncio.CancelledError:
            logger.debug(f"Redis pubsub task for {channel} cancelled")
        except Exception as e:
            logger.error(f"Redis pubsub error for {channel}: {e}")
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()
    
    async def cache_set(
        self,
        key: str,
        value: Union[str, dict, list],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a value in Redis cache."""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            await self.redis.set(key, value, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def cache_get(self, key: str) -> Optional[Union[str, dict, list]]:
        """Get a value from Redis cache."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    async def cache_delete(self, key: str) -> bool:
        """Delete a key from Redis cache."""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def cache_exists(self, key: str) -> bool:
        """Check if a key exists in Redis cache."""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    async def increment_counter(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment a counter in Redis."""
        try:
            value = await self.redis.incrby(key, amount)
            if ttl and value == amount:  # First time setting
                await self.redis.expire(key, ttl)
            return value
        except Exception as e:
            logger.error(f"Failed to increment counter {key}: {e}")
            return 0
    
    async def get_counter(self, key: str) -> int:
        """Get a counter value from Redis."""
        try:
            value = await self.redis.get(key)
            return int(value) if value else 0
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to get counter {key}: {e}")
            return 0
    
    async def set_user_presence(
        self,
        user_id: str,
        status: str = "online",
        ttl: int = 300,
    ) -> bool:
        """Set user presence status."""
        key = f"presence:{user_id}"
        return await self.cache_set(key, {"status": status, "last_seen": asyncio.get_event_loop().time()}, ttl)
    
    async def get_user_presence(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user presence status."""
        key = f"presence:{user_id}"
        return await self.cache_get(key)
    
    async def cleanup_expired_keys(self, pattern: str) -> int:
        """Clean up expired keys matching a pattern."""
        try:
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                
                if keys:
                    deleted_count += await self.redis.delete(*keys)
                
                if cursor == 0:
                    break
            
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys {pattern}: {e}")
            return 0


class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> tuple[bool, Dict[str, int]]:
        """Check if an action is allowed under rate limit."""
        try:
            redis = self.redis_manager.redis
            now = int(asyncio.get_event_loop().time())
            pipeline = redis.pipeline()
            
            pipeline.zremrangebyscore(key, 0, now - window)
            pipeline.zcard(key)
            pipeline.zadd(key, {str(now): now})
            pipeline.expire(key, window)
            
            results = await pipeline.execute()
            current_requests = results[1]
            
            if current_requests < limit:
                return True, {
                    "allowed": True,
                    "remaining": limit - current_requests - 1,
                    "reset_time": now + window,
                }
            else:
                await redis.zrem(key, str(now))
                return False, {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": now + window,
                }
        
        except Exception as e:
            logger.error(f"Rate limiter error for key {key}: {e}")
            return True, {"allowed": True, "remaining": limit, "reset_time": 0}


# Global Redis manager instance
redis_manager = RedisManager()