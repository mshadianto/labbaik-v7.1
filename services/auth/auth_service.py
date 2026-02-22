"""
LABBAIK AI v6.0 - Authentication Service
========================================
Complete authentication service with Google OAuth, email/password, and session management.
"""

from __future__ import annotations
import os
import jwt
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from core.config import get_settings
from core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    SessionExpiredError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AuthToken:
    """Authentication token container."""
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "bearer"
    expires_in: int = 3600
    expires_at: datetime = None
    
    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(seconds=self.expires_in)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at.isoformat(),
        }


@dataclass
class AuthUser:
    """Authenticated user information."""
    id: str
    email: str
    name: str
    role: str = "user"
    avatar_url: Optional[str] = None
    provider: str = "local"  # local, google
    is_verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "avatar_url": self.avatar_url,
            "provider": self.provider,
            "is_verified": self.is_verified,
        }


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    user: AuthUser
    token: AuthToken
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
    
    def update_activity(self):
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, max_inactive_hours: int = 24) -> bool:
        inactive_time = datetime.utcnow() - self.last_activity
        return inactive_time > timedelta(hours=max_inactive_hours)


# =============================================================================
# PASSWORD UTILITIES
# =============================================================================

class PasswordService:
    """Password hashing and verification service."""
    
    ROUNDS = 12  # bcrypt rounds
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=cls.ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @classmethod
    def verify_password(cls, password: str, hashed: str) -> bool:
        """Verify a password against a hash."""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception:
            return False
    
    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password minimal 8 karakter"
        
        if not any(c.isupper() for c in password):
            return False, "Password harus mengandung huruf besar"
        
        if not any(c.islower() for c in password):
            return False, "Password harus mengandung huruf kecil"
        
        if not any(c.isdigit() for c in password):
            return False, "Password harus mengandung angka"
        
        return True, ""


# =============================================================================
# JWT SERVICE
# =============================================================================

class JWTService:
    """JWT token generation and validation service."""
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
    ):
        settings = get_settings()
        
        self.secret_key = secret_key or settings.auth.jwt_secret_key
        self.algorithm = algorithm or settings.auth.jwt_algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)
        
        if not self.secret_key:
            logger.warning("JWT secret key not configured, using random key")
            self.secret_key = secrets.token_hex(32)
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str = "user",
        additional_claims: Dict = None
    ) -> str:
        """Create a new access token."""
        now = datetime.utcnow()
        expires = now + self.access_token_expire
        
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "iat": now,
            "exp": expires,
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a new refresh token."""
        now = datetime.utcnow()
        expires = now + self.refresh_token_expire
        
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": expires,
            "jti": secrets.token_hex(16),  # Unique token ID
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_token_pair(
        self,
        user_id: str,
        email: str,
        role: str = "user"
    ) -> AuthToken:
        """Create access and refresh token pair."""
        access_token = self.create_access_token(user_id, email, role)
        refresh_token = self.create_refresh_token(user_id)
        
        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(self.access_token_expire.total_seconds()),
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Raises:
            TokenExpiredError: If token has expired
            AuthenticationError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token telah kadaluarsa")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Token tidak valid: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> AuthToken:
        """
        Refresh an access token using a refresh token.
        
        Returns:
            New AuthToken with fresh access token
        """
        payload = self.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        user_id = payload.get("sub")
        
        # Note: In production, fetch user details from database
        # to get current email and role
        access_token = self.create_access_token(
            user_id=user_id,
            email="",  # Should be fetched from DB
            role="user"  # Should be fetched from DB
        )
        
        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=int(self.access_token_expire.total_seconds()),
        )


# =============================================================================
# GOOGLE OAUTH SERVICE
# =============================================================================

class GoogleOAuthService:
    """Google OAuth 2.0 authentication service."""
    
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
    ):
        settings = get_settings()
        
        self.client_id = client_id or settings.auth.google_client_id
        self.client_secret = client_secret or settings.auth.google_client_secret
        self.redirect_uri = redirect_uri or settings.auth.google_redirect_uri
        
        self._configured = bool(self.client_id and self.client_secret)
    
    @property
    def is_configured(self) -> bool:
        return self._configured
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
        
        Returns:
            Authorization URL to redirect user to
        """
        if not self._configured:
            raise AuthenticationError("Google OAuth not configured")
        
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_URL}?{query_string}"
    
    async def exchange_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from Google
        
        Returns:
            Token response from Google
        """
        import httpx
        
        if not self._configured:
            raise AuthenticationError("Google OAuth not configured")
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.text}")
                raise AuthenticationError("Failed to authenticate with Google")
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> AuthUser:
        """
        Get user information from Google.
        
        Args:
            access_token: Google access token
        
        Returns:
            AuthUser with Google user information
        """
        import httpx
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise AuthenticationError("Failed to get user info from Google")
            
            data = response.json()
            
            return AuthUser(
                id=data["id"],
                email=data["email"],
                name=data.get("name", data["email"].split("@")[0]),
                avatar_url=data.get("picture"),
                provider="google",
                is_verified=data.get("verified_email", False),
            )
    
    async def authenticate(self, code: str) -> Tuple[AuthUser, Dict[str, Any]]:
        """
        Complete Google OAuth flow.
        
        Args:
            code: Authorization code from Google
        
        Returns:
            Tuple of (AuthUser, token_data)
        """
        token_data = await self.exchange_code(code)
        user = await self.get_user_info(token_data["access_token"])
        
        return user, token_data


# =============================================================================
# SESSION MANAGER
# =============================================================================

class SessionManager:
    """In-memory session manager for Streamlit."""
    
    def __init__(self, max_sessions_per_user: int = 5):
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, list] = {}  # user_id -> [session_ids]
        self.max_sessions_per_user = max_sessions_per_user
    
    def create_session(
        self,
        user: AuthUser,
        token: AuthToken,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Session:
        """Create a new session for user."""
        session_id = secrets.token_urlsafe(32)
        
        session = Session(
            session_id=session_id,
            user_id=user.id,
            user=user,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Clean up old sessions for this user
        self._cleanup_user_sessions(user.id)
        
        # Store session
        self._sessions[session_id] = session
        
        if user.id not in self._user_sessions:
            self._user_sessions[user.id] = []
        self._user_sessions[user.id].append(session_id)
        
        logger.info(f"Session created for user {user.id}: {session_id[:8]}...")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        
        if session and session.is_expired():
            self.destroy_session(session_id)
            return None
        
        if session:
            session.update_activity()
        
        return session
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        session = self._sessions.pop(session_id, None)
        
        if session:
            user_sessions = self._user_sessions.get(session.user_id, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
            
            logger.info(f"Session destroyed: {session_id[:8]}...")
            return True
        
        return False
    
    def destroy_user_sessions(self, user_id: str):
        """Destroy all sessions for a user."""
        session_ids = self._user_sessions.pop(user_id, [])
        
        for session_id in session_ids:
            self._sessions.pop(session_id, None)
        
        logger.info(f"All sessions destroyed for user {user_id}")
    
    def _cleanup_user_sessions(self, user_id: str):
        """Remove oldest sessions if user has too many."""
        session_ids = self._user_sessions.get(user_id, [])
        
        while len(session_ids) >= self.max_sessions_per_user:
            oldest_id = session_ids.pop(0)
            self._sessions.pop(oldest_id, None)
            logger.debug(f"Cleaned up old session: {oldest_id[:8]}...")


# =============================================================================
# MAIN AUTH SERVICE
# =============================================================================

class AuthService:
    """
    Main authentication service combining all auth methods.
    """
    
    def __init__(self):
        self.jwt_service = JWTService()
        self.google_oauth = GoogleOAuthService()
        self.session_manager = SessionManager()
        self._user_store: Dict[str, Dict] = {}  # Simple in-memory store for demo
    
    # -------------------------------------------------------------------------
    # Email/Password Authentication
    # -------------------------------------------------------------------------
    
    def register(
        self,
        email: str,
        password: str,
        name: str,
        phone: str = None,
    ) -> Tuple[AuthUser, AuthToken]:
        """
        Register a new user with email/password.
        
        Returns:
            Tuple of (AuthUser, AuthToken)
        """
        # Validate password
        is_valid, error = PasswordService.validate_password_strength(password)
        if not is_valid:
            raise AuthenticationError(error)
        
        # Check if email exists
        if email.lower() in self._user_store:
            raise AuthenticationError("Email sudah terdaftar")
        
        # Create user
        user_id = secrets.token_hex(16)
        password_hash = PasswordService.hash_password(password)
        
        user_data = {
            "id": user_id,
            "email": email.lower(),
            "name": name,
            "phone": phone,
            "password_hash": password_hash,
            "role": "user",
            "provider": "local",
            "is_verified": False,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self._user_store[email.lower()] = user_data
        
        # Create auth objects
        user = AuthUser(
            id=user_id,
            email=email.lower(),
            name=name,
            role="user",
            provider="local",
            is_verified=False,
        )
        
        token = self.jwt_service.create_token_pair(
            user_id=user_id,
            email=email.lower(),
            role="user"
        )
        
        logger.info(f"New user registered: {email}")
        
        return user, token
    
    def login(self, email: str, password: str) -> Tuple[AuthUser, AuthToken]:
        """
        Authenticate user with email/password.
        
        Returns:
            Tuple of (AuthUser, AuthToken)
        """
        user_data = self._user_store.get(email.lower())
        
        if not user_data:
            raise InvalidCredentialsError("Email atau password salah")
        
        if not PasswordService.verify_password(password, user_data["password_hash"]):
            raise InvalidCredentialsError("Email atau password salah")
        
        # Create auth objects
        user = AuthUser(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            provider=user_data["provider"],
            is_verified=user_data["is_verified"],
        )
        
        token = self.jwt_service.create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        
        logger.info(f"User logged in: {email}")
        
        return user, token
    
    def logout(self, session_id: str) -> bool:
        """Logout user by destroying session."""
        return self.session_manager.destroy_session(session_id)
    
    # -------------------------------------------------------------------------
    # Token Validation
    # -------------------------------------------------------------------------
    
    def validate_token(self, token: str) -> AuthUser:
        """
        Validate access token and return user.
        
        Returns:
            AuthUser from token
        """
        payload = self.jwt_service.verify_token(token)
        
        return AuthUser(
            id=payload["sub"],
            email=payload.get("email", ""),
            name=payload.get("name", ""),
            role=payload.get("role", "user"),
        )
    
    def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh access token."""
        return self.jwt_service.refresh_access_token(refresh_token)
    
    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------
    
    def create_session(
        self,
        user: AuthUser,
        token: AuthToken,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Session:
        """Create authenticated session."""
        return self.session_manager.create_session(
            user=user,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self.session_manager.get_session(session_id)
    
    # -------------------------------------------------------------------------
    # Google OAuth
    # -------------------------------------------------------------------------
    
    def get_google_auth_url(self) -> str:
        """Get Google OAuth authorization URL."""
        return self.google_oauth.get_authorization_url()
    
    async def handle_google_callback(
        self, 
        code: str
    ) -> Tuple[AuthUser, AuthToken]:
        """
        Handle Google OAuth callback.
        
        Returns:
            Tuple of (AuthUser, AuthToken)
        """
        google_user, google_tokens = await self.google_oauth.authenticate(code)
        
        # Check if user exists
        existing_user = self._user_store.get(google_user.email.lower())
        
        if existing_user:
            # Update existing user with Google info
            existing_user["avatar_url"] = google_user.avatar_url
            existing_user["is_verified"] = True
            user_id = existing_user["id"]
            role = existing_user["role"]
        else:
            # Create new user
            user_id = google_user.id
            role = "user"
            
            self._user_store[google_user.email.lower()] = {
                "id": user_id,
                "email": google_user.email.lower(),
                "name": google_user.name,
                "password_hash": None,  # No password for OAuth users
                "role": role,
                "provider": "google",
                "avatar_url": google_user.avatar_url,
                "is_verified": True,
                "created_at": datetime.utcnow().isoformat(),
            }
        
        # Create our own tokens
        user = AuthUser(
            id=user_id,
            email=google_user.email,
            name=google_user.name,
            role=role,
            avatar_url=google_user.avatar_url,
            provider="google",
            is_verified=True,
        )
        
        token = self.jwt_service.create_token_pair(
            user_id=user_id,
            email=google_user.email,
            role=role
        )
        
        logger.info(f"Google OAuth login: {google_user.email}")
        
        return user, token


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the authentication service singleton."""
    global _auth_service
    
    if _auth_service is None:
        _auth_service = AuthService()
    
    return _auth_service
