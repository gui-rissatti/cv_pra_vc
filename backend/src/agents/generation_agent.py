"""Agent for generating application materials using LLMs."""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from core.llm_provider import LLMProvider, get_llm_provider
from core.scoring import calculate_heuristic_score
from prompts import (
    COVER_LETTER_PROMPT,
    CV_GENERATION_PROMPT,
    INSIGHTS_PROMPT,
    NETWORKING_PROMPT,
)

LOGGER = structlog.get_logger(__name__)


@dataclass(slots=True)
class GeneratedBundle:
    """Container for all generated assets."""

    cv: str
    cover_letter: str
    networking: str
    insights: str
    match_score: int
    generated_at: datetime


class GenerationAgent:
    """Orchestrates the generation of CVs, cover letters, and insights."""

    def __init__(
        self,
        *,
        llm_provider: LLMProvider | None = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.4,
    ) -> None:
        """
        Initialize GenerationAgent.

        Args:
            llm_provider: LLM provider instance. If None, creates default Gemini provider.
            model: Model name (used if creating default provider)
            temperature: Temperature for LLM generation
        """
        self._llm_provider = llm_provider or get_llm_provider("gemini", model=model)
        self._temperature = temperature

    async def generate_all(
        self,
        job_data: dict[str, Any],
        cv_text: str,
        language: str = "auto",
        tone: str = "professional",
        variance: int = 3,
    ) -> GeneratedBundle:
        """Generate all materials in parallel."""

        LOGGER.info(
            "generation_agent.start",
            job_title=job_data.get("title"),
            language=language,
            tone=tone,
            variance=variance,
        )

        # Detect language if auto
        target_language = self._resolve_language(
            job_data.get("description", ""), language
        )

        # Prepare inputs
        inputs = {
            "job_title": job_data.get("title", ""),
            "job_company": job_data.get("company", ""),
            "job_description": job_data.get("description", ""),
            "job_skills": ", ".join(job_data.get("skills", [])),
            "candidate_cv": cv_text,
            "target_language": target_language,
            "tone": tone,
            "variance_level": variance,
        }

        # Build prompts
        cv_prompt = CV_GENERATION_PROMPT.format(**inputs)
        cl_prompt = COVER_LETTER_PROMPT.format(**inputs)
        net_prompt = NETWORKING_PROMPT.format(**inputs)
        insights_prompt = INSIGHTS_PROMPT.format(**inputs)

        # Execute in parallel
        try:
            results = await asyncio.gather(
                self._generate_with_retry(cv_prompt),
                self._generate_with_retry(cl_prompt),
                self._generate_with_retry(net_prompt),
                self._generate_with_retry(insights_prompt),
            )
        except Exception as exc:
            LOGGER.error("generation_agent.failed", error=str(exc))
            raise RuntimeError(f"Generation failed: {exc}") from exc

        cv_result, cl_result, net_result, insights_text = results

        # Debug logging to ensure correct assignment
        LOGGER.debug(
            "generation_agent.results",
            cv_start=cv_result[:50] if cv_result else "empty",
            cl_start=cl_result[:50] if cl_result else "empty",
            net_start=net_result[:50] if net_result else "empty",
            insights_start=insights_text[:50] if insights_text else "empty",
        )

        # Extract score from insights text
        llm_score = self._extract_score_from_insights(insights_text)

        # Fallback to heuristic if extraction fails
        if llm_score == 0:
            heuristic_score = calculate_heuristic_score(
                job_data.get("skills", []), cv_text
            )
            llm_score = heuristic_score
            LOGGER.warning(
                "generation_agent.score_extraction_failed",
                using_heuristic=heuristic_score,
            )
        else:
            heuristic_score = calculate_heuristic_score(
                job_data.get("skills", []), cv_text
            )
            LOGGER.debug("generation_agent.scores", llm=llm_score, heuristic=heuristic_score)

        return GeneratedBundle(
            cv=cv_result,
            cover_letter=cl_result,
            networking=net_result,
            insights=insights_text,
            match_score=llm_score,
            generated_at=datetime.now(timezone.utc),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _generate_with_retry(self, prompt: str) -> str:
        """Generate text with retry logic."""
        return await self._llm_provider.generate(prompt, temperature=self._temperature)

    def _extract_score_from_insights(self, insights_text: str) -> int:
        """Extract compatibility score from formatted insights text."""
        # Look for patterns like "Compatibilidade: 85/100" or "Compatibility: 85/100"
        patterns = [
            r"Compatibilidade:\s*(\d+)/100",
            r"Compatibility:\s*(\d+)/100",
            r"Compatibilité:\s*(\d+)/100",
            r"Compatibilidad:\s*(\d+)/100",
            r"##\s*\w+:\s*(\d+)/100",  # Generic heading with score
        ]
        
        for pattern in patterns:
            match = re.search(pattern, insights_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                return max(0, min(100, score))  # Clamp to 0-100
        
        return 0  # Return 0 if no score found

    def _resolve_language(self, description: str, language: str) -> str:
        """Detect or return the target language for outputs."""
        if language != "auto":
            return language

        # Simple heuristic: check for common words
        desc_lower = description.lower()

        # Portuguese indicators
        if any(
            word in desc_lower
            for word in ["você", "será", "responsável", "conhecimento", "experiência"]
        ):
            return "pt"

        # Spanish indicators
        if any(
            word in desc_lower
            for word in ["usted", "será", "responsable", "conocimiento", "experiencia"]
        ):
            return "es"

        # French indicators
        if any(
            word in desc_lower
            for word in ["vous", "serez", "responsable", "connaissance", "expérience"]
        ):
            return "fr"

        # Default to English
        return "en"
