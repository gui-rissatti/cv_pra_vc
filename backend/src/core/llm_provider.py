"""Abstract LLM provider interface for vendor-agnostic LLM access."""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

import structlog

LOGGER = structlog.get_logger(__name__)


class LLMProvider(ABC):
    """Interface abstrata para provedores de LLM."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.4,
        **kwargs: Any,
    ) -> str:
        """
        Gera texto usando LLM.

        Args:
            prompt: Prompt para o LLM
            temperature: Temperatura para geração (0.0-1.0)
            **kwargs: Argumentos adicionais específicos do provider

        Returns:
            Texto gerado

        Raises:
            RuntimeError: Se a geração falhar
        """
        pass

    @abstractmethod
    async def generate_parallel(
        self,
        prompts: list[str],
        temperature: float = 0.4,
        **kwargs: Any,
    ) -> list[str]:
        """
        Gera múltiplos textos em paralelo.

        Args:
            prompts: Lista de prompts
            temperature: Temperatura para geração
            **kwargs: Argumentos adicionais

        Returns:
            Lista de textos gerados (mesma ordem dos inputs)

        Raises:
            RuntimeError: Se alguma geração falhar
        """
        pass


class GeminiProvider(LLMProvider):
    """Implementação using Google Gemini via LangChain."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
    ) -> None:
        """
        Inicializa Gemini provider.

        Args:
            api_key: Google API key
            model: Modelo Gemini a usar

        Raises:
            ImportError: Se langchain-google-genai não está instalado
            ValueError: Se api_key está vazio
        """
        if not api_key:
            raise ValueError("google_api_key cannot be empty")

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise ImportError(
                "langchain-google-genai is required. "
                "Install it with: pip install langchain-google-genai"
            ) from exc

        self._api_key = api_key
        self._model = model
        self._llm_class = ChatGoogleGenerativeAI

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.4,
        **kwargs: Any,
    ) -> str:
        """Gera texto usando Gemini."""
        llm = self._llm_class(
            model=self._model,
            temperature=temperature,
            google_api_key=self._api_key,
            convert_system_message_to_human=True,
        )

        try:
            result = await llm.ainvoke(prompt)
            return result.content
        except Exception as exc:
            LOGGER.error(
                "gemini_generation_failed",
                model=self._model,
                error=str(exc),
            )
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc

    async def generate_parallel(
        self,
        prompts: list[str],
        temperature: float = 0.4,
        **kwargs: Any,
    ) -> list[str]:
        """Gera múltiplos textos em paralelo via Gemini."""
        tasks = [
            self.generate(prompt, temperature=temperature, **kwargs)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)


class MockLLMProvider(LLMProvider):
    """Mock implementation para testes."""

    def __init__(self, response: str = "Mock response") -> None:
        """
        Inicializa mock provider.

        Args:
            response: Resposta fixa para retornar
        """
        self._response = response

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.4,
        **kwargs: Any,
    ) -> str:
        """Retorna resposta mock."""
        LOGGER.debug("mock_llm.generate", prompt_length=len(prompt))
        return self._response

    async def generate_parallel(
        self,
        prompts: list[str],
        temperature: float = 0.4,
        **kwargs: Any,
    ) -> list[str]:
        """Retorna lista de respostas mock."""
        LOGGER.debug("mock_llm.generate_parallel", count=len(prompts))
        return [self._response] * len(prompts)


def get_llm_provider(
    provider_name: str = "gemini",
    **kwargs: Any,
) -> LLMProvider:
    """
    Factory para criar LLM provider.

    Args:
        provider_name: Nome do provider ("gemini" ou "mock")
        **kwargs: Argumentos específicos do provider

    Returns:
        Instância do provider

    Raises:
        ValueError: Se provider_name é desconhecido
    """
    if provider_name == "gemini":
        from core.config import get_settings

        settings = get_settings()
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required for Gemini provider. "
                "Set it via .env file or GOOGLE_API_KEY environment variable."
            )

        return GeminiProvider(
            api_key=settings.google_api_key,
            model=kwargs.get("model", "gemini-2.5-flash"),
        )

    elif provider_name == "mock":
        return MockLLMProvider(
            response=kwargs.get("response", "Mock response")
        )

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            "Supported: 'gemini', 'mock'"
        )


__all__ = [
    "LLMProvider",
    "GeminiProvider",
    "MockLLMProvider",
    "get_llm_provider",
]
