"""User service for CRUD operations."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.password import password_manager
from models.user import User

if TYPE_CHECKING:
    pass


class UserService:
    """Service for user-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def get_by_id(self, user_id: str | UUID) -> User | None:
        """Get user by ID."""
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self._session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email.lower(),
            password_hash=password_manager.hash(password),
            full_name=full_name,
            email_verified=False,
            is_active=True,
            is_superuser=False,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> User | None:
        """Authenticate a user with email and password."""
        user = await self.get_by_email(email)
        if user is None:
            return None
        if user.password_hash is None:
            return None
        if not password_manager.verify(password, user.password_hash):
            return None
        return user

    async def update_last_login(self, user: User) -> None:
        """Update the user's last login timestamp."""
        user.last_login_at = datetime.now(UTC)
        await self._session.flush()

    async def deactivate(self, user: User) -> None:
        """Deactivate a user account."""
        user.is_active = False
        await self._session.flush()

    async def activate(self, user: User) -> None:
        """Activate a user account."""
        user.is_active = True
        await self._session.flush()

    async def verify_email(self, user: User) -> None:
        """Mark user email as verified."""
        user.email_verified = True
        await self._session.flush()
