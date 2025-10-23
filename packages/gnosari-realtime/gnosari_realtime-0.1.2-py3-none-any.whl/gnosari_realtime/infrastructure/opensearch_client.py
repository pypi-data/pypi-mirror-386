"""OpenSearch client for message indexing and search."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from opensearchpy import OpenSearch, exceptions

from ..core.schemas import Message
from ..server.config import settings


logger = logging.getLogger(__name__)


class OpenSearchManager:
    """Manages OpenSearch connections and indexing operations."""
    
    def __init__(self, opensearch_url: Optional[str] = None):
        self.opensearch_url = opensearch_url or settings.opensearch_url
        self._client: Optional[OpenSearch] = None
        self.message_index = "gnosari-messages"
        self.connection_index = "gnosari-connections"
    
    async def connect(self) -> None:
        """Connect to OpenSearch."""
        if self._client is None:
            self._client = OpenSearch(
                hosts=[self.opensearch_url],
                use_ssl=False,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True,
            )
        
        try:
            info = await self._client.info()
            logger.info(f"Connected to OpenSearch: {info['version']['number']}")
            await self._create_indices()
        except Exception as e:
            logger.error(f"Failed to connect to OpenSearch: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from OpenSearch."""
        if self._client:
            await self._client.close()
            self._client = None
        logger.info("Disconnected from OpenSearch")
    
    @property
    def client(self) -> OpenSearch:
        """Get the OpenSearch client."""
        if self._client is None:
            raise RuntimeError("OpenSearch not connected. Call connect() first.")
        return self._client
    
    async def _create_indices(self) -> None:
        """Create OpenSearch indices with mappings."""
        await self._create_message_index()
        await self._create_connection_index()
    
    async def _create_message_index(self) -> None:
        """Create the message index with proper mappings."""
        mapping = {
            "mappings": {
                "properties": {
                    "message_id": {"type": "keyword"},
                    "channel": {"type": "keyword"},
                    "message_type": {"type": "keyword"},
                    "action": {"type": "keyword"},
                    "version": {"type": "keyword"},
                    "payload": {"type": "object", "enabled": True},
                    "metadata": {"type": "object", "enabled": True},
                    "user_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "team_id": {"type": "keyword"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "timestamp": {"type": "date"},
                    "indexed_at": {"type": "date"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index": {
                    "max_result_window": 50000
                }
            }
        }
        
        try:
            if not await self.client.indices.exists(index=self.message_index):
                await self.client.indices.create(index=self.message_index, body=mapping)
                logger.info(f"Created OpenSearch index: {self.message_index}")
        except Exception as e:
            logger.error(f"Failed to create message index: {e}")
    
    async def _create_connection_index(self) -> None:
        """Create the connection index with proper mappings."""
        mapping = {
            "mappings": {
                "properties": {
                    "connection_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "connected_at": {"type": "date"},
                    "disconnected_at": {"type": "date"},
                    "duration": {"type": "long"},
                    "metadata": {"type": "object", "enabled": True},
                    "indexed_at": {"type": "date"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        }
        
        try:
            if not await self.client.indices.exists(index=self.connection_index):
                await self.client.indices.create(index=self.connection_index, body=mapping)
                logger.info(f"Created OpenSearch index: {self.connection_index}")
        except Exception as e:
            logger.error(f"Failed to create connection index: {e}")
    
    async def index_message(self, message: Message, channel: str) -> bool:
        """Index a message in OpenSearch."""
        try:
            doc = {
                "message_id": message.id,
                "channel": channel,
                "message_type": message.type.value,
                "action": message.action,
                "version": message.version,
                "payload": message.payload,
                "metadata": message.metadata.model_dump() if message.metadata else None,
                "user_id": message.metadata.user_id if message.metadata else None,
                "session_id": message.metadata.session_id if message.metadata else None,
                "team_id": message.metadata.team_id if message.metadata else None,
                "content": self._extract_searchable_content(message),
                "timestamp": message.metadata.timestamp if message.metadata else datetime.utcnow(),
                "indexed_at": datetime.utcnow(),
            }
            
            await self.client.index(
                index=self.message_index,
                id=message.id,
                body=doc,
                refresh=False,
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to index message {message.id}: {e}")
            return False
    
    async def search_messages(
        self,
        query: str,
        channel: Optional[str] = None,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        message_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        size: int = 100,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """Search messages in OpenSearch."""
        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": [],
                        "filter": [],
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": size,
                "from": from_,
            }
            
            if query:
                search_body["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": ["content", "payload.*", "action"],
                        "type": "best_fields",
                    }
                })
            
            if not search_body["query"]["bool"]["must"]:
                search_body["query"]["bool"]["must"].append({"match_all": {}})
            
            if channel:
                search_body["query"]["bool"]["filter"].append({"term": {"channel": channel}})
            
            if user_id:
                search_body["query"]["bool"]["filter"].append({"term": {"user_id": user_id}})
            
            if team_id:
                search_body["query"]["bool"]["filter"].append({"term": {"team_id": team_id}})
            
            if message_type:
                search_body["query"]["bool"]["filter"].append({"term": {"message_type": message_type}})
            
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time.isoformat()
                if end_time:
                    time_range["lte"] = end_time.isoformat()
                
                search_body["query"]["bool"]["filter"].append({"range": {"timestamp": time_range}})
            
            response = await self.client.search(
                index=self.message_index,
                body=search_body,
            )
            
            return {
                "hits": response["hits"]["hits"],
                "total": response["hits"]["total"]["value"],
                "took": response["took"],
            }
        
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return {"hits": [], "total": 0, "took": 0}
    
    async def get_message_analytics(
        self,
        channel: Optional[str] = None,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get message analytics and aggregations."""
        try:
            search_body = {
                "size": 0,
                "query": {
                    "bool": {
                        "filter": []
                    }
                },
                "aggs": {
                    "messages_over_time": {
                        "date_histogram": {
                            "field": "timestamp",
                            "calendar_interval": "1h",
                            "min_doc_count": 0,
                        }
                    },
                    "by_channel": {
                        "terms": {
                            "field": "channel",
                            "size": 20,
                        }
                    },
                    "by_message_type": {
                        "terms": {
                            "field": "message_type",
                            "size": 10,
                        }
                    },
                    "by_action": {
                        "terms": {
                            "field": "action",
                            "size": 20,
                        }
                    },
                    "active_users": {
                        "cardinality": {
                            "field": "user_id"
                        }
                    },
                }
            }
            
            if channel:
                search_body["query"]["bool"]["filter"].append({"term": {"channel": channel}})
            
            if user_id:
                search_body["query"]["bool"]["filter"].append({"term": {"user_id": user_id}})
            
            if team_id:
                search_body["query"]["bool"]["filter"].append({"term": {"team_id": team_id}})
            
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time.isoformat()
                if end_time:
                    time_range["lte"] = end_time.isoformat()
                
                search_body["query"]["bool"]["filter"].append({"range": {"timestamp": time_range}})
            
            response = await self.client.search(
                index=self.message_index,
                body=search_body,
            )
            
            return {
                "total_messages": response["hits"]["total"]["value"],
                "time_series": response["aggregations"]["messages_over_time"]["buckets"],
                "by_channel": response["aggregations"]["by_channel"]["buckets"],
                "by_message_type": response["aggregations"]["by_message_type"]["buckets"],
                "by_action": response["aggregations"]["by_action"]["buckets"],
                "active_users": response["aggregations"]["active_users"]["value"],
            }
        
        except Exception as e:
            logger.error(f"Failed to get message analytics: {e}")
            return {
                "total_messages": 0,
                "time_series": [],
                "by_channel": [],
                "by_message_type": [],
                "by_action": [],
                "active_users": 0,
            }
    
    async def index_connection_event(
        self,
        connection_id: str,
        event_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index a connection event."""
        try:
            doc = {
                "connection_id": connection_id,
                "event_type": event_type,
                "user_id": user_id,
                "session_id": session_id,
                "metadata": metadata,
                "timestamp": datetime.utcnow(),
                "indexed_at": datetime.utcnow(),
            }
            
            doc_id = f"{connection_id}_{event_type}_{datetime.utcnow().timestamp()}"
            
            await self.client.index(
                index=self.connection_index,
                id=doc_id,
                body=doc,
                refresh=False,
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to index connection event: {e}")
            return False
    
    async def cleanup_old_documents(self, days: int = 30) -> Dict[str, int]:
        """Delete documents older than specified days."""
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
        deleted_counts = {}
        
        for index_name in [self.message_index, self.connection_index]:
            try:
                query = {
                    "query": {
                        "range": {
                            "indexed_at": {
                                "lt": cutoff_date.isoformat()
                            }
                        }
                    }
                }
                
                response = await self.client.delete_by_query(
                    index=index_name,
                    body=query,
                    refresh=True,
                )
                
                deleted_counts[index_name] = response.get("deleted", 0)
                
            except Exception as e:
                logger.error(f"Failed to cleanup old documents in {index_name}: {e}")
                deleted_counts[index_name] = 0
        
        return deleted_counts
    
    def _extract_searchable_content(self, message: Message) -> str:
        """Extract searchable text content from a message."""
        content_parts = []
        
        if message.action:
            content_parts.append(message.action)
        
        def extract_from_dict(data: Dict[str, Any], prefix: str = "") -> None:
            for key, value in data.items():
                if isinstance(value, str) and len(value) < 1000:
                    content_parts.append(f"{prefix}{key}: {value}")
                elif isinstance(value, dict):
                    extract_from_dict(value, f"{prefix}{key}.")
                elif isinstance(value, (int, float, bool)):
                    content_parts.append(f"{prefix}{key}: {str(value)}")
        
        if message.payload:
            extract_from_dict(message.payload)
        
        if message.metadata:
            metadata_dict = message.metadata.model_dump()
            extract_from_dict(metadata_dict, "meta.")
        
        return " ".join(content_parts)


# Global OpenSearch manager instance
opensearch_manager = OpenSearchManager()