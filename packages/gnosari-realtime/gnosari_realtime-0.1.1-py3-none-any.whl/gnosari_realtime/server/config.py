"""Server configuration management."""

import os
from typing import Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database Configuration
    database_url: str = "postgresql+asyncpg://gnosari:gnosari123@localhost:5432/gnosari_realtime"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # OpenSearch Configuration
    opensearch_url: str = "http://localhost:9200"
    
    # JWT Configuration
    jwt_secret_key: str = "your-jwt-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    log_level: str = "INFO"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    max_connections_per_client: int = 5
    
    # Message Configuration
    max_message_size: int = 1048576  # 1MB
    max_channel_name_length: int = 100
    
    # Optional Gnosari Integration
    gnosari_enabled: bool = False
    gnosari_api_url: Optional[str] = None
    gnosari_api_key: Optional[str] = None
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v: str, values) -> str:
        """Ensure JWT secret is set in production."""
        debug = values.get("debug", True)
        if not debug and v == "your-jwt-secret-key-change-this-in-production":
            raise ValueError("JWT secret key must be changed in production")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is supported."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()