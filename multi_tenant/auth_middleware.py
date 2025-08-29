"""
JWT-based tenant authentication middleware for multi-tenant RAG system.

Provides secure tenant isolation through JWT tokens with embedded tenant claims,
request validation, and session management.
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

import jwt
from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import logging

from .tenant_models import AuthToken, TenantSession, TenantConfig

logger = logging.getLogger(__name__)


class TenantAuthenticationError(Exception):
    """Custom exception for tenant authentication errors."""
    pass


class TenantAuthorizationError(Exception):
    """Custom exception for tenant authorization errors."""
    pass


class JWTTenantAuth:
    """
    JWT-based tenant authentication and authorization manager.
    
    Provides secure multi-tenant authentication with tenant context
    embedded in JWT tokens and comprehensive request validation.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        token_expire_hours: int = 24,
        refresh_expire_days: int = 30
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_hours = token_expire_hours
        self.refresh_expire_days = refresh_expire_days
        
        # Password hashing context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # HTTP Bearer security scheme
        self.security = HTTPBearer(auto_error=False)
        
        # In-memory session store (use Redis in production)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("JWT Tenant Auth initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        permissions: List[str] = None,
        session_id: Optional[str] = None,
        custom_claims: Dict[str, Any] = None
    ) -> str:
        """
        Create JWT access token with tenant context.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            permissions: User permissions list
            session_id: Optional session identifier
            custom_claims: Additional claims to include
            
        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.token_expire_hours)
        
        payload = {
            # Standard JWT claims
            "iat": now.timestamp(),
            "exp": expires_at.timestamp(),
            "sub": user_id,  # Subject (user)
            
            # Tenant-specific claims
            "tenant_id": tenant_id,
            "user_id": user_id,
            "permissions": permissions or ["read"],
            "session_id": session_id,
            
            # Token metadata
            "token_type": "access",
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        # Add custom claims
        if custom_claims:
            payload.update(custom_claims)
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created access token for user {user_id}, tenant {tenant_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise TenantAuthenticationError(f"Failed to create access token: {str(e)}")
    
    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Create JWT refresh token for token renewal.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            session_id: Optional session identifier
            
        Returns:
            JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self.refresh_expire_days)
        
        payload = {
            "iat": now.timestamp(),
            "exp": expires_at.timestamp(),
            "sub": user_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "session_id": session_id,
            "token_type": "refresh",
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created refresh token for user {user_id}, tenant {tenant_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise TenantAuthenticationError(f"Failed to create refresh token: {str(e)}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            TenantAuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            # Validate required claims
            required_claims = ["user_id", "tenant_id", "exp", "iat"]
            for claim in required_claims:
                if claim not in payload:
                    raise TenantAuthenticationError(f"Missing required claim: {claim}")
            
            # Check if token is expired (additional check)
            exp_timestamp = payload.get("exp", 0)
            if datetime.fromtimestamp(exp_timestamp, timezone.utc) <= datetime.now(timezone.utc):
                raise TenantAuthenticationError("Token has expired")
            
            logger.debug(f"Token verified for user {payload.get('user_id')}, tenant {payload.get('tenant_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            raise TenantAuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise TenantAuthenticationError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise TenantAuthenticationError(f"Token verification failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access and refresh tokens
        """
        try:
            payload = self.verify_token(refresh_token)
            
            # Verify this is a refresh token
            if payload.get("token_type") != "refresh":
                raise TenantAuthenticationError("Invalid token type for refresh")
            
            # Create new tokens
            new_access_token = self.create_access_token(
                user_id=payload["user_id"],
                tenant_id=payload["tenant_id"],
                permissions=payload.get("permissions", ["read"]),
                session_id=payload.get("session_id")
            )
            
            new_refresh_token = self.create_refresh_token(
                user_id=payload["user_id"],
                tenant_id=payload["tenant_id"],
                session_id=payload.get("session_id")
            )
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise TenantAuthenticationError(f"Failed to refresh token: {str(e)}")
    
    async def authenticate_request(self, request: Request) -> Dict[str, Any]:
        """
        Authenticate HTTP request and extract tenant context.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Authentication context with user and tenant info
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Extract Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Validate Bearer token format
            if not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Bearer token required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Extract token
            token = auth_header.split(" ", 1)[1]
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not found",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Verify token
            try:
                payload = self.verify_token(token)
            except TenantAuthenticationError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Validate session if present
            session_id = payload.get("session_id")
            if session_id:
                session_valid = await self.validate_session(session_id, payload["tenant_id"])
                if not session_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session expired or invalid"
                    )
            
            # Build authentication context
            auth_context = {
                "user_id": payload["user_id"],
                "tenant_id": payload["tenant_id"],
                "permissions": payload.get("permissions", ["read"]),
                "session_id": session_id,
                "token_payload": payload,
                "authenticated": True
            }
            
            # Add to request state for downstream access
            request.state.auth_context = auth_context
            
            logger.debug(f"Request authenticated: user={payload['user_id']}, tenant={payload['tenant_id']}")
            return auth_context
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication processing error"
            )
    
    async def validate_session(self, session_id: str, tenant_id: str) -> bool:
        """
        Validate session exists and is active.
        
        Args:
            session_id: Session identifier
            tenant_id: Tenant identifier
            
        Returns:
            True if session is valid
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                logger.debug(f"Session not found: {session_id}")
                return False
            
            # Check tenant match
            if session.get("tenant_id") != tenant_id:
                logger.warning(f"Session tenant mismatch: {session_id}")
                return False
            
            # Check expiration
            expires_at = session.get("expires_at")
            if expires_at and datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc):
                logger.debug(f"Session expired: {session_id}")
                self.active_sessions.pop(session_id, None)
                return False
            
            # Update last activity
            session["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False
    
    async def create_session(
        self,
        user_id: str,
        tenant_id: str,
        timeout_hours: int = 24,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Create new session.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            timeout_hours: Session timeout in hours
            metadata: Additional session metadata
            
        Returns:
            Session ID
        """
        import uuid
        
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=timeout_hours)
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        
        self.active_sessions[session_id] = session_data
        
        logger.info(f"Created session {session_id} for user {user_id}, tenant {tenant_id}")
        return session_id
    
    async def terminate_session(self, session_id: str) -> bool:
        """
        Terminate session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was terminated
        """
        session = self.active_sessions.pop(session_id, None)
        if session:
            logger.info(f"Terminated session {session_id}")
            return True
        return False
    
    def check_permission(self, auth_context: Dict[str, Any], required_permission: str) -> bool:
        """
        Check if user has required permission.
        
        Args:
            auth_context: Authentication context from authenticate_request
            required_permission: Required permission string
            
        Returns:
            True if user has permission
        """
        user_permissions = auth_context.get("permissions", [])
        
        # Admin permission grants all access
        if "admin" in user_permissions:
            return True
        
        # Check specific permission
        if required_permission in user_permissions:
            return True
        
        # Check wildcard permissions
        permission_parts = required_permission.split(":")
        for i in range(len(permission_parts)):
            wildcard_permission = ":".join(permission_parts[:i+1]) + ":*"
            if wildcard_permission in user_permissions:
                return True
        
        logger.debug(f"Permission denied: user permissions {user_permissions}, required {required_permission}")
        return False
    
    def require_permission(self, required_permission: str):
        """
        Decorator to require specific permission for endpoint.
        
        Args:
            required_permission: Required permission string
        """
        def decorator(func):
            async def wrapper(request: Request, *args, **kwargs):
                auth_context = getattr(request.state, 'auth_context', None)
                if not auth_context:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not self.check_permission(auth_context, required_permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission required: {required_permission}"
                    )
                
                return await func(request, *args, **kwargs)
            
            return wrapper
        return decorator
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now(timezone.utc)
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            expires_at_str = session.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at <= now:
                    expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            self.active_sessions.pop(session_id, None)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)


# FastAPI dependency functions

def get_auth_manager() -> JWTTenantAuth:
    """Get JWT tenant auth manager instance."""
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    return JWTTenantAuth(secret_key=secret_key)


async def get_current_user(
    request: Request,
    auth_manager: JWTTenantAuth = Security(get_auth_manager)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.
    
    Returns:
        Authentication context with user and tenant info
    """
    return await auth_manager.authenticate_request(request)


async def get_tenant_context(
    auth_context: Dict[str, Any] = Security(get_current_user)
) -> str:
    """
    FastAPI dependency to get tenant ID from authenticated request.
    
    Returns:
        Tenant ID string
    """
    return auth_context["tenant_id"]


def require_tenant_permission(permission: str):
    """
    FastAPI dependency to require specific tenant permission.
    
    Args:
        permission: Required permission string
    """
    async def permission_dependency(
        auth_context: Dict[str, Any] = Security(get_current_user),
        auth_manager: JWTTenantAuth = Security(get_auth_manager)
    ) -> Dict[str, Any]:
        if not auth_manager.check_permission(auth_context, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return auth_context
    
    return permission_dependency


# Usage Example and Testing Functions

async def example_usage():
    """Example usage of JWT tenant authentication."""
    # Initialize auth manager
    secret_key = "your-super-secret-key-keep-it-safe"
    auth = JWTTenantAuth(secret_key=secret_key)
    
    # Create session
    session_id = await auth.create_session(
        user_id="john_doe",
        tenant_id="client_abc",
        metadata={"login_source": "web_app"}
    )
    
    # Create access token
    access_token = auth.create_access_token(
        user_id="john_doe",
        tenant_id="client_abc",
        permissions=["read", "write", "documents:*"],
        session_id=session_id
    )
    
    # Create refresh token
    refresh_token = auth.create_refresh_token(
        user_id="john_doe",
        tenant_id="client_abc",
        session_id=session_id
    )
    
    print(f"Session ID: {session_id}")
    print(f"Access Token: {access_token[:50]}...")
    print(f"Refresh Token: {refresh_token[:50]}...")
    
    # Verify token
    try:
        payload = auth.verify_token(access_token)
        print(f"Token valid for user: {payload['user_id']}, tenant: {payload['tenant_id']}")
        
        # Check permissions
        auth_context = {
            "user_id": payload["user_id"],
            "tenant_id": payload["tenant_id"],
            "permissions": payload["permissions"]
        }
        
        can_read_docs = auth.check_permission(auth_context, "documents:read")
        can_delete_docs = auth.check_permission(auth_context, "documents:delete")
        
        print(f"Can read documents: {can_read_docs}")
        print(f"Can delete documents: {can_delete_docs}")
        
    except TenantAuthenticationError as e:
        print(f"Token verification failed: {e}")
    
    # Refresh token
    try:
        new_tokens = auth.refresh_access_token(refresh_token)
        print(f"New access token: {new_tokens['access_token'][:50]}...")
        
    except TenantAuthenticationError as e:
        print(f"Token refresh failed: {e}")
    
    # Clean up
    await auth.terminate_session(session_id)
    print(f"Session {session_id} terminated")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())