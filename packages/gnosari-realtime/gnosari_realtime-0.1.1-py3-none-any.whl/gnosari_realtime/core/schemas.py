"""Message schemas and validation models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class MessageType(str, Enum):
    """Message type enumeration."""
    
    COMMAND = "command"
    QUERY = "query"
    EVENT = "event"
    RESPONSE = "response"
    ERROR = "error"


class MessageMetadata(BaseModel):
    """Message metadata container."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    team_id: Optional[str] = None


class Message(BaseModel):
    """Core message schema for WebSocket communication."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType
    action: str
    version: str = "v1"
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    
    @validator("action")
    def validate_action(cls, v: str) -> str:
        """Validate action is not empty."""
        if not v.strip():
            raise ValueError("Action cannot be empty")
        return v.strip()


class SubscriptionMessage(BaseModel):
    """Message for channel subscription requests."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.COMMAND
    action: str = "subscribe"
    version: str = "v1"
    payload: Dict[str, Any] = Field(...)
    
    @validator("payload")
    def validate_subscription_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate subscription payload has required channel field."""
        if "channel" not in v:
            raise ValueError("Subscription payload must include 'channel' field")
        if not isinstance(v["channel"], str) or not v["channel"].strip():
            raise ValueError("Channel must be a non-empty string")
        return v


class UnsubscriptionMessage(BaseModel):
    """Message for channel unsubscription requests."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.COMMAND
    action: str = "unsubscribe"
    version: str = "v1"
    payload: Dict[str, Any] = Field(...)
    
    @validator("payload")
    def validate_unsubscription_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate unsubscription payload has required channel field."""
        if "channel" not in v:
            raise ValueError("Unsubscription payload must include 'channel' field")
        if not isinstance(v["channel"], str) or not v["channel"].strip():
            raise ValueError("Channel must be a non-empty string")
        return v


class PublishMessage(BaseModel):
    """Message for publishing to channels."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.EVENT
    action: str = "publish"
    version: str = "v1"
    payload: Dict[str, Any] = Field(...)
    
    @validator("payload")
    def validate_publish_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate publish payload has required fields."""
        if "channel" not in v:
            raise ValueError("Publish payload must include 'channel' field")
        if "data" not in v:
            raise ValueError("Publish payload must include 'data' field")
        if not isinstance(v["channel"], str) or not v["channel"].strip():
            raise ValueError("Channel must be a non-empty string")
        return v


class ErrorMessage(BaseModel):
    """Error message schema."""
    
    id: str
    type: MessageType = MessageType.ERROR
    action: str = "error"
    version: str = "v1"
    payload: Dict[str, Any] = Field(...)
    
    @validator("payload")
    def validate_error_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate error payload structure."""
        required_fields = ["code", "message"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Error payload must include '{field}' field")
        return v


class ChatMessage(BaseModel):
    """Chat-specific message schema."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.COMMAND
    action: str = "send_chat_message"
    version: str = "v1"
    payload: Dict[str, Any] = Field(...)
    
    @validator("payload")
    def validate_chat_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate chat payload structure."""
        required_fields = ["message", "team_id"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Chat payload must include '{field}' field")
        
        if not isinstance(v["message"], str) or not v["message"].strip():
            raise ValueError("Message must be a non-empty string")
        if not isinstance(v["team_id"], str) or not v["team_id"].strip():
            raise ValueError("Team ID must be a non-empty string")
        
        return v


class VoiceMessage(BaseModel):
    """Voice message schema."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.COMMAND
    action: str = "send_voice_message"
    version: str = "v1"
    payload: Dict[str, Any] = Field(...)
    
    @validator("payload")
    def validate_voice_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate voice payload structure."""
        required_fields = ["audio_data", "team_id"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Voice payload must include '{field}' field")
        
        if not isinstance(v["audio_data"], str):
            raise ValueError("Audio data must be a base64-encoded string")
        if not isinstance(v["team_id"], str) or not v["team_id"].strip():
            raise ValueError("Team ID must be a non-empty string")
        
        return v


class AgentResponseMessage(BaseModel):
    """Agent response message schema."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: MessageType = MessageType.EVENT
    action: str = "agent_response"
    version: str = "v1"
    payload: Dict[str, Any] = Field(...)
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    
    @validator("payload")
    def validate_agent_response_payload(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent response payload structure."""
        required_fields = ["agent_name", "content"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Agent response payload must include '{field}' field")
        return v