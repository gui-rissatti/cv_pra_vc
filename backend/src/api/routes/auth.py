"""Authentication API routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth.dependencies import (
    get_current_user,
    get_jwt_manager,
    get_user_service,
)
from auth.jwt import InvalidTokenError, JWTManager
from auth.schemas import (
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from models.user import User
from services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Register a new user with email and password."""
    existing_user = await user_service.get_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await user_service.create(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
) -> TokenResponse:
    """Login with email and password to obtain access and refresh tokens."""
    user = await user_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    await user_service.update_last_login(user)

    # Generate tokens
    access_token = jwt_manager.create_access_token({"sub": str(user.id)})
    refresh_token = jwt_manager.create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> TokenResponse:
    """Refresh access token using a valid refresh token."""
    try:
        token_payload = jwt_manager.verify_token(payload.refresh_token)

        if token_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = token_payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Verify user still exists and is active
        user = await user_service.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new access token
        access_token = jwt_manager.create_access_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=None,
            token_type="bearer",
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current authenticated user information."""
    return current_user


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageResponse:
    """Logout the current user.

    Note: In a stateless JWT setup, the client should discard the tokens.
    For full token invalidation, implement a token blacklist using Redis.
    """
    # In a stateless JWT setup, the client discards tokens
    # For a more complete implementation, add tokens to a Redis blacklist
    return MessageResponse(message="Successfully logged out")
