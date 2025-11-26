"""Application configuration handling."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource, PydanticBaseSettingsSource


DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://localhost:5174"]

# Get backend root directory (where .env file lives)
_BACKEND_ROOT = Path(__file__).parent.parent.parent
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """Centralized application settings sourced from environment variables."""

    environment: str = "development"
    api_port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: DEFAULT_CORS_ORIGINS.copy())
    
    # Rate Limits
    rate_limit_extraction: str = "10/minute"
    rate_limit_generation: str = "5/minute"

    # Security
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "*.onrender.com", "testserver"]

    # External APIs
    google_api_key: str | None = None
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str | None = None

    # Database
    database_url: str | None = None

    # Redis
    redis_url: str | None = None

    # JWT Settings
    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @staticmethod
    def _normalize_origins(value: object) -> list[str] | object:
        if isinstance(value, str):
            parts = [chunk.strip() for chunk in value.split(",") if chunk.strip()]
            return parts or DEFAULT_CORS_ORIGINS
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> list[str]:
        normalized = cls._normalize_origins(value)
        if isinstance(normalized, list):
            return normalized
        return DEFAULT_CORS_ORIGINS

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        class _CorsAwareEnv(env_settings.__class__):
            def decode_complex_value(self, field_name: str, field: Any, value: Any) -> Any:  # type: ignore[override]
                if field_name == "cors_origins" and isinstance(value, str):
                    normalized = cls._normalize_origins(value)
                    if isinstance(normalized, list):
                        return normalized
                return super().decode_complex_value(field_name, field, value)

        class _CorsAwareDotEnv(dotenv_settings.__class__):
            def decode_complex_value(self, field_name: str, field: Any, value: Any) -> Any:  # type: ignore[override]
                if field_name == "cors_origins" and isinstance(value, str):
                    normalized = cls._normalize_origins(value)
                    if isinstance(normalized, list):
                        return normalized
                return super().decode_complex_value(field_name, field, value)

        wrapped_env = _CorsAwareEnv(
            settings_cls,
            case_sensitive=getattr(env_settings, "case_sensitive", None),
            env_prefix=getattr(env_settings, "env_prefix", None),
            env_nested_delimiter=getattr(env_settings, "env_nested_delimiter", None),
        )
        wrapped_dotenv = _CorsAwareDotEnv(
            settings_cls,
            env_file=getattr(dotenv_settings, "env_file", None),
            env_file_encoding=getattr(dotenv_settings, "env_file_encoding", None),
            case_sensitive=getattr(dotenv_settings, "case_sensitive", None),
            env_prefix=getattr(dotenv_settings, "env_prefix", None),
            env_nested_delimiter=getattr(dotenv_settings, "env_nested_delimiter", None),
        )

        return (
            init_settings,
            wrapped_env,
            wrapped_dotenv,
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def _cached_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached settings instance (useful for tests)."""
    _cached_settings.cache_clear()


def get_settings(*, cache: bool = True) -> Settings:
    """Return the settings instance, optionally bypassing the cache."""
    if not cache:
        reset_settings_cache()
    return _cached_settings()
