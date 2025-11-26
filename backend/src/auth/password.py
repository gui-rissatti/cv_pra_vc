"""Password hashing utilities."""
from __future__ import annotations

from passlib.context import CryptContext


class PasswordManager:
    """Handles password hashing and verification."""

    def __init__(self, schemes: list[str] | None = None) -> None:
        """Initialize the password context with bcrypt as default."""
        self._context = CryptContext(
            schemes=schemes or ["bcrypt"],
            deprecated="auto",
        )

    def hash(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self._context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return self._context.verify(plain_password, hashed_password)


# Default singleton instance
password_manager = PasswordManager()
