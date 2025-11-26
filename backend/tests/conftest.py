"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Add src directory to path for imports
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _BACKEND_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


def _load_env_file() -> None:
    """Load .env from backend root if present, fallback to environment."""
    env_file = _BACKEND_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def load_env() -> None:
    """Ensure environment variables are available for every test session."""
    _load_env_file()


@pytest.fixture(scope="session")
def require_gemini_key() -> None:
    """Skip integration tests when GOOGLE_API_KEY is missing."""
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip(
            "GOOGLE_API_KEY não configurada. "
            "Crie backend/.env com sua chave da Google antes de executar testes."
        )
