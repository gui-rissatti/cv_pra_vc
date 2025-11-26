"""JWT token management."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt


class InvalidTokenError(Exception):
    """Raised when a token is invalid or expired."""

    pass


class JWTManager:
    """Handles JWT token creation and verification."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ) -> None:
        """Initialize JWT manager with configuration."""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create an access token with optional custom expiry."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a refresh token with optional custom expiry."""
        to_encode = data.copy()
        expire = datetime.now(UTC) + (
            expires_delta or timedelta(days=self.refresh_token_expire_days)
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise InvalidTokenError("Invalid or expired token") from None

    def get_token_type(self, token: str) -> str | None:
        """Get the type of token (access or refresh)."""
        try:
            payload = self.verify_token(token)
            return payload.get("type")
        except InvalidTokenError:
            return None
