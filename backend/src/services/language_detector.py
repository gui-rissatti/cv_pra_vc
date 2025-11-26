"""Language detection from text using heuristics."""
from __future__ import annotations

import structlog

LOGGER = structlog.get_logger(__name__)


class LanguageDetector:
    """Detects language from text using keyword heuristics."""

    # Language-specific keywords for detection
    PORTUGUESE_WORDS = {
        "você",
        "será",
        "responsável",
        "conhecimento",
        "experiência",
        "requisito",
        "desenvolvedor",
        "sistema",
        "equipe",
        "trabalho",
    }

    SPANISH_WORDS = {
        "usted",
        "será",
        "responsable",
        "conocimiento",
        "experiencia",
        "requisito",
        "desarrollador",
        "sistema",
        "equipo",
        "trabajo",
    }

    FRENCH_WORDS = {
        "vous",
        "serez",
        "responsable",
        "connaissance",
        "expérience",
        "requis",
        "développeur",
        "système",
        "équipe",
        "travail",
    }

    def detect(self, text: str, default: str = "en") -> str:
        """
        Detect language from text.

        Uses simple keyword matching heuristic to detect language.
        Returns language code with highest keyword match count.

        Supported languages:
        - pt: Portuguese
        - es: Spanish
        - fr: French
        - en: English (default)

        Args:
            text: Text to analyze
            default: Default language if detection fails

        Returns:
            Language code (pt, es, fr, en)
        """
        if not text:
            LOGGER.debug("language_detector.empty_text", returning=default)
            return default

        text_lower = text.lower()

        # Count keyword matches for each language
        pt_count = sum(1 for word in self.PORTUGUESE_WORDS if word in text_lower)
        es_count = sum(1 for word in self.SPANISH_WORDS if word in text_lower)
        fr_count = sum(1 for word in self.FRENCH_WORDS if word in text_lower)

        # Determine language with highest match count
        counts = {"pt": pt_count, "es": es_count, "fr": fr_count}
        detected = max(counts, key=counts.get)

        # Use detected language if it has matches, otherwise default
        result = detected if counts[detected] > 0 else default

        LOGGER.debug(
            "language_detector.detected",
            text_length=len(text),
            detected=result,
            pt_score=pt_count,
            es_score=es_count,
            fr_score=fr_count,
        )

        return result

    @staticmethod
    def format_language_name(code: str) -> str:
        """
        Get human-readable language name from code.

        Args:
            code: Language code (pt, es, fr, en)

        Returns:
            Language name
        """
        names = {
            "pt": "Portuguese",
            "es": "Spanish",
            "fr": "French",
            "en": "English",
        }
        return names.get(code, "Unknown")


__all__ = ["LanguageDetector"]
