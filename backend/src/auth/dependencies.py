"""FastAPI dependencies for authentication."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from auth.jwt import InvalidTokenError, JWTManager
from core.config import get_settings
from core.database import AsyncSession, get_db_session
from services.user_service import UserService

if TYPE_CHECKING:
    from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance."""
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret key not configured",
        )
    return JWTManager(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    settings = get_settings()
    if not settings.database_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database URL not configured",
        )
    async for session in get_db_session(settings.database_url):
        yield session


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserService:
    """Get user service instance."""
    return UserService(session)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Extract and validate user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt_manager.verify_token(token)
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if user_id is None:
            raise credentials_exception
        if token_type != "access":
            raise credentials_exception
    except InvalidTokenError as exc:
        raise credentials_exception from exc

    user = await user_service.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return user


async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme_optional)],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User | None:
    """Return user if authenticated, None otherwise."""
    if token is None:
        return None
    try:
        payload = jwt_manager.verify_token(token)
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if user_id is None or token_type != "access":
            return None

        user = await user_service.get_by_id(user_id)
        if user is None or not user.is_active:
            return None
        return user
    except InvalidTokenError:
        return None
