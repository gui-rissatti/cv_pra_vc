"""Tests for password hashing."""
from __future__ import annotations

from auth.password import PasswordManager, password_manager


class TestPasswordManager:
    """Test suite for PasswordManager."""

    def test_hash_returns_different_from_plain(self) -> None:
        """Password hash should differ from plain password."""
        plain = "test_password123"
        hashed = password_manager.hash(plain)
        assert hashed != plain

    def test_hash_is_deterministic_per_instance(self) -> None:
        """Different hashes for same password due to salt."""
        plain = "test_password123"
        hash1 = password_manager.hash(plain)
        hash2 = password_manager.hash(plain)
        # bcrypt generates unique salts each time
        assert hash1 != hash2

    def test_verify_correct_password(self) -> None:
        """Verify should return True for correct password."""
        plain = "test_password123"
        hashed = password_manager.hash(plain)
        assert password_manager.verify(plain, hashed) is True

    def test_verify_incorrect_password(self) -> None:
        """Verify should return False for incorrect password."""
        plain = "test_password123"
        hashed = password_manager.hash(plain)
        assert password_manager.verify("wrong_password", hashed) is False

    def test_verify_empty_password(self) -> None:
        """Verify should handle empty passwords."""
        hashed = password_manager.hash("test_password123")
        assert password_manager.verify("", hashed) is False

    def test_custom_schemes(self) -> None:
        """PasswordManager can be initialized with custom schemes."""
        manager = PasswordManager(schemes=["bcrypt"])
        plain = "test_password"
        hashed = manager.hash(plain)
        assert manager.verify(plain, hashed) is True

    def test_hash_special_characters(self) -> None:
        """Hash should handle special characters in passwords."""
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = password_manager.hash(special_password)
        assert password_manager.verify(special_password, hashed) is True

    def test_hash_unicode_characters(self) -> None:
        """Hash should handle unicode characters in passwords."""
        unicode_password = "Senhaséçura123"
        hashed = password_manager.hash(unicode_password)
        assert password_manager.verify(unicode_password, hashed) is True
