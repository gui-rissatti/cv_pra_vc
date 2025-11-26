"""Tests for JWT token management."""
from __future__ import annotations

from datetime import timedelta

import pytest

from auth.jwt import InvalidTokenError, JWTManager


class TestJWTManager:
    """Test suite for JWTManager."""

    @pytest.fixture
    def jwt_manager(self) -> JWTManager:
        """Create a JWT manager for testing."""
        return JWTManager(
            secret_key="test-secret-key-for-testing-only",
            algorithm="HS256",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )

    def test_create_access_token(self, jwt_manager: JWTManager) -> None:
        """Access token should be created and decodable."""
        data = {"sub": "user123"}
        token = jwt_manager.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        payload = jwt_manager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_create_refresh_token(self, jwt_manager: JWTManager) -> None:
        """Refresh token should be created with correct type."""
        data = {"sub": "user123"}
        token = jwt_manager.create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

        payload = jwt_manager.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    def test_access_token_expiry(self, jwt_manager: JWTManager) -> None:
        """Access token should include exp claim."""
        data = {"sub": "user123"}
        token = jwt_manager.create_access_token(data)
        payload = jwt_manager.verify_token(token)

        assert "exp" in payload

    def test_custom_expiry_delta(self, jwt_manager: JWTManager) -> None:
        """Token should respect custom expiry delta."""
        data = {"sub": "user123"}
        token = jwt_manager.create_access_token(
            data,
            expires_delta=timedelta(minutes=5),
        )
        payload = jwt_manager.verify_token(token)

        assert "exp" in payload

    def test_verify_invalid_token(self, jwt_manager: JWTManager) -> None:
        """Verify should raise for invalid tokens."""
        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token("invalid-token")

    def test_verify_tampered_token(self, jwt_manager: JWTManager) -> None:
        """Verify should raise for tampered tokens."""
        data = {"sub": "user123"}
        token = jwt_manager.create_access_token(data)

        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1] + "tampered"
        tampered_token = ".".join(parts)

        with pytest.raises(InvalidTokenError):
            jwt_manager.verify_token(tampered_token)

    def test_verify_wrong_secret(self) -> None:
        """Verify should fail with wrong secret key."""
        manager1 = JWTManager(secret_key="secret1")
        manager2 = JWTManager(secret_key="secret2")

        token = manager1.create_access_token({"sub": "user123"})

        with pytest.raises(InvalidTokenError):
            manager2.verify_token(token)

    def test_get_token_type_access(self, jwt_manager: JWTManager) -> None:
        """get_token_type should return 'access' for access tokens."""
        token = jwt_manager.create_access_token({"sub": "user123"})
        assert jwt_manager.get_token_type(token) == "access"

    def test_get_token_type_refresh(self, jwt_manager: JWTManager) -> None:
        """get_token_type should return 'refresh' for refresh tokens."""
        token = jwt_manager.create_refresh_token({"sub": "user123"})
        assert jwt_manager.get_token_type(token) == "refresh"

    def test_get_token_type_invalid(self, jwt_manager: JWTManager) -> None:
        """get_token_type should return None for invalid tokens."""
        assert jwt_manager.get_token_type("invalid-token") is None

    def test_token_contains_custom_claims(self, jwt_manager: JWTManager) -> None:
        """Tokens should preserve custom claims in data."""
        data = {"sub": "user123", "custom_claim": "custom_value"}
        token = jwt_manager.create_access_token(data)
        payload = jwt_manager.verify_token(token)

        assert payload["custom_claim"] == "custom_value"

    def test_expired_token_raises(self) -> None:
        """Expired token should raise InvalidTokenError."""
        manager = JWTManager(
            secret_key="test-secret",
            access_token_expire_minutes=0,  # Immediate expiration
        )

        # Create token with very short expiry
        token = manager.create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        with pytest.raises(InvalidTokenError):
            manager.verify_token(token)
