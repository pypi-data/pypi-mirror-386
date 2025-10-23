"""JWT authentication and authorization."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import jwt
from pydantic import BaseModel, validator
from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser
from starlette.requests import Request

from .config import settings


logger = logging.getLogger(__name__)


class UserClaims(BaseModel):
    """JWT user claims model."""
    
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    teams: List[str] = []
    permissions: List[str] = []
    is_admin: bool = False
    
    @validator("user_id")
    def validate_user_id(cls, v: str) -> str:
        """Validate user ID is not empty."""
        if not v.strip():
            raise ValueError("User ID cannot be empty")
        return v.strip()


class AuthenticatedUser(SimpleUser):
    """Extended user class with additional claims."""
    
    def __init__(self, username: str, claims: UserClaims):
        super().__init__(username)
        self.claims = claims
        self.user_id = claims.user_id
        self.teams = claims.teams
        self.permissions = claims.permissions
        self.is_admin = claims.is_admin
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return self.is_admin or permission in self.permissions
    
    def has_team_access(self, team_id: str) -> bool:
        """Check if user has access to a specific team."""
        return self.is_admin or team_id in self.teams
    
    def can_access_channel(self, channel: str) -> bool:
        """Check if user can access a specific channel."""
        if self.is_admin:
            return True
        
        if channel.startswith("team:"):
            team_id = channel[5:]  # Remove "team:" prefix
            return self.has_team_access(team_id)
        
        if channel.startswith("user:"):
            user_id = channel[5:]  # Remove "user:" prefix
            return user_id == self.user_id
        
        return channel.startswith("public:")


class JWTTokenManager:
    """JWT token management."""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes
    
    def create_token(self, user_claims: UserClaims) -> str:
        """Create a JWT token for a user."""
        now = datetime.utcnow()
        payload = {
            "sub": user_claims.user_id,
            "username": user_claims.username,
            "email": user_claims.email,
            "teams": user_claims.teams,
            "permissions": user_claims.permissions,
            "is_admin": user_claims.is_admin,
            "iat": now,
            "exp": now + timedelta(minutes=self.expire_minutes),
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[UserClaims]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            claims = UserClaims(
                user_id=payload["sub"],
                username=payload.get("username"),
                email=payload.get("email"),
                teams=payload.get("teams", []),
                permissions=payload.get("permissions", []),
                is_admin=payload.get("is_admin", False),
            )
            
            return claims
        
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
        except Exception as e:
            logger.error(f"Error decoding JWT token: {e}")
        
        return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh a JWT token if it's still valid."""
        claims = self.decode_token(token)
        if claims:
            return self.create_token(claims)
        return None


class JWTAuthenticationBackend(AuthenticationBackend):
    """Starlette authentication backend for JWT."""
    
    def __init__(self):
        self.token_manager = JWTTokenManager()
    
    async def authenticate(self, request: Request) -> Optional[tuple[AuthCredentials, AuthenticatedUser]]:
        """Authenticate a request using JWT."""
        token = self._extract_token(request)
        if not token:
            return None
        
        claims = self.token_manager.decode_token(token)
        if not claims:
            return None
        
        user = AuthenticatedUser(
            username=claims.username or claims.user_id,
            claims=claims,
        )
        
        credentials = AuthCredentials(["authenticated"])
        if claims.is_admin:
            credentials.scopes.append("admin")
        
        return credentials, user
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers or query params."""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        return request.query_params.get("token")


class ChannelAuthorizationManager:
    """Manages channel access authorization."""
    
    def __init__(self):
        self.channel_patterns = {
            "public": lambda user, channel: True,
            "user": lambda user, channel: self._check_user_channel(user, channel),
            "team": lambda user, channel: self._check_team_channel(user, channel),
            "admin": lambda user, channel: user.is_admin,
        }
    
    def can_subscribe(self, user: Optional[AuthenticatedUser], channel: str) -> bool:
        """Check if a user can subscribe to a channel."""
        if not user:
            return channel.startswith("public:")
        
        return user.can_access_channel(channel)
    
    def can_publish(self, user: Optional[AuthenticatedUser], channel: str) -> bool:
        """Check if a user can publish to a channel."""
        if not user:
            return False
        
        if channel.startswith("public:"):
            return user.has_permission("publish_public")
        
        return user.can_access_channel(channel)
    
    def _check_user_channel(self, user: AuthenticatedUser, channel: str) -> bool:
        """Check user-specific channel access."""
        if not channel.startswith("user:"):
            return False
        
        target_user_id = channel[5:]  # Remove "user:" prefix
        return user.user_id == target_user_id or user.is_admin
    
    def _check_team_channel(self, user: AuthenticatedUser, channel: str) -> bool:
        """Check team-specific channel access."""
        if not channel.startswith("team:"):
            return False
        
        team_id = channel[5:]  # Remove "team:" prefix
        return user.has_team_access(team_id)


class AuthService:
    """Main authentication service."""
    
    def __init__(self):
        self.token_manager = JWTTokenManager()
        self.auth_backend = JWTAuthenticationBackend()
        self.channel_auth = ChannelAuthorizationManager()
    
    async def authenticate_websocket(self, websocket) -> Optional[AuthenticatedUser]:
        """Authenticate a WebSocket connection."""
        token = None
        
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
        
        if not token:
            token = websocket.query_params.get("token")
        
        if not token:
            return None
        
        claims = self.token_manager.decode_token(token)
        if not claims:
            return None
        
        return AuthenticatedUser(
            username=claims.username or claims.user_id,
            claims=claims,
        )
    
    def create_user_token(
        self,
        user_id: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        teams: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        is_admin: bool = False,
    ) -> str:
        """Create a JWT token for a user."""
        claims = UserClaims(
            user_id=user_id,
            username=username,
            email=email,
            teams=teams or [],
            permissions=permissions or [],
            is_admin=is_admin,
        )
        
        return self.token_manager.create_token(claims)
    
    def can_user_subscribe(self, user: Optional[AuthenticatedUser], channel: str) -> bool:
        """Check if user can subscribe to a channel."""
        return self.channel_auth.can_subscribe(user, channel)
    
    def can_user_publish(self, user: Optional[AuthenticatedUser], channel: str) -> bool:
        """Check if user can publish to a channel."""
        return self.channel_auth.can_publish(user, channel)


# Global auth service instance
auth_service = AuthService()