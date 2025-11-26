"""Tests for auth schemas."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from auth.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


class TestRegisterRequest:
    """Test suite for RegisterRequest schema."""

    def test_valid_registration(self) -> None:
        """Valid registration data should pass validation."""
        request = RegisterRequest(
            email="test@example.com",
            password="password123",
            full_name="Test User",
        )
        assert request.email == "test@example.com"
        assert request.password == "password123"
        assert request.full_name == "Test User"

    def test_email_required(self) -> None:
        """Email should be required."""
        with pytest.raises(ValidationError):
            RegisterRequest(password="password123")  # type: ignore[call-arg]

    def test_password_required(self) -> None:
        """Password should be required."""
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com")  # type: ignore[call-arg]

    def test_password_min_length(self) -> None:
        """Password must be at least 8 characters."""
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="short")

    def test_invalid_email(self) -> None:
        """Invalid email should fail validation."""
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="password123")

    def test_full_name_optional(self) -> None:
        """Full name should be optional."""
        request = RegisterRequest(email="test@example.com", password="password123")
        assert request.full_name is None


class TestLoginRequest:
    """Test suite for LoginRequest schema."""

    def test_valid_login(self) -> None:
        """Valid login data should pass validation."""
        request = LoginRequest(email="test@example.com", password="password123")
        assert request.email == "test@example.com"
        assert request.password == "password123"

    def test_email_required(self) -> None:
        """Email should be required."""
        with pytest.raises(ValidationError):
            LoginRequest(password="password123")  # type: ignore[call-arg]

    def test_password_required(self) -> None:
        """Password should be required."""
        with pytest.raises(ValidationError):
            LoginRequest(email="test@example.com")  # type: ignore[call-arg]


class TestTokenResponse:
    """Test suite for TokenResponse schema."""

    def test_with_refresh_token(self) -> None:
        """TokenResponse should include refresh token."""
        response = TokenResponse(
            access_token="access123",
            refresh_token="refresh456",
        )
        assert response.access_token == "access123"
        assert response.refresh_token == "refresh456"
        assert response.token_type == "bearer"

    def test_without_refresh_token(self) -> None:
        """TokenResponse should work without refresh token."""
        response = TokenResponse(access_token="access123")
        assert response.access_token == "access123"
        assert response.refresh_token is None
        assert response.token_type == "bearer"


class TestRefreshTokenRequest:
    """Test suite for RefreshTokenRequest schema."""

    def test_valid_request(self) -> None:
        """Valid refresh token request should pass."""
        request = RefreshTokenRequest(refresh_token="token123")
        assert request.refresh_token == "token123"

    def test_refresh_token_required(self) -> None:
        """Refresh token should be required."""
        with pytest.raises(ValidationError):
            RefreshTokenRequest()  # type: ignore[call-arg]


class TestUserResponse:
    """Test suite for UserResponse schema."""

    def test_from_attributes(self) -> None:
        """UserResponse should work with from_attributes."""

        class MockUser:
            id = uuid4()
            email = "test@example.com"
            email_verified = True
            full_name = "Test User"
            avatar_url = None
            is_active = True
            is_superuser = False
            created_at = datetime.now(UTC)
            updated_at = datetime.now(UTC)
            last_login_at = None

        response = UserResponse.model_validate(MockUser())
        assert response.email == "test@example.com"
        assert response.email_verified is True
        assert response.full_name == "Test User"


class TestMessageResponse:
    """Test suite for MessageResponse schema."""

    def test_message(self) -> None:
        """MessageResponse should contain message."""
        response = MessageResponse(message="Success")
        assert response.message == "Success"
