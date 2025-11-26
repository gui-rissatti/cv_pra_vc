"""Pydantic schemas for authentication."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str


class UserResponse(BaseModel):
    """Response model for user data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    email_verified: bool
    full_name: str | None
    avatar_url: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


class UserCreate(BaseModel):
    """Internal model for creating users."""

    email: str
    password_hash: str
    full_name: str | None = None
    email_verified: bool = False
    is_active: bool = True
    is_superuser: bool = False


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
