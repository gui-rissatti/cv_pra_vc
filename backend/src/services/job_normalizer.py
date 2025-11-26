"""Job data normalization and deduplication service."""
from __future__ import annotations

from typing import Iterable

import structlog

from services.scraper import ScrapedJob

LOGGER = structlog.get_logger(__name__)


class JobNormalizer:
    """Normalizes and merges job data from scraper and LLM outputs."""

    @staticmethod
    def merge_with_llm_output(
        original: ScrapedJob,
        llm_output: dict,
    ) -> ScrapedJob:
        """
        Merge scraped job with structured output from LLM.

        Priority:
        - Use LLM output if available and non-empty
        - Fall back to original scraped data

        Args:
            original: Job data from scraper
            llm_output: Structured data from LLM (typically Pydantic model as dict)

        Returns:
            Merged ScrapedJob with normalized data
        """
        # Extract skills, preferring LLM output
        skills = llm_output.get("skills") or original.skills
        deduped_skills = JobNormalizer.dedupe_strings(skills, strip=True)

        # Build merged job with LLM data taking precedence
        merged = ScrapedJob(
            url=original.url,
            board=original.board,
            title=llm_output.get("title") or original.title,
            company=llm_output.get("company") or original.company,
            description=llm_output.get("description") or original.description,
            skills=deduped_skills,
            raw_html=original.raw_html,
            company_extraction_method=original.company_extraction_method,
        )

        LOGGER.debug(
            "job_normalizer.merged",
            title=merged.title,
            company=merged.company,
            skills_count=len(merged.skills),
        )

        return merged

    @staticmethod
    def dedupe_strings(
        values: Iterable[str],
        *,
        strip: bool = True,
        lowercase_key: bool = True,
    ) -> list[str]:
        """
        Remove duplicated strings (case-insensitive).

        Args:
            values: Iterable of strings to deduplicate
            strip: If True, call .strip() on each value
            lowercase_key: If True, use lowercase for comparison

        Returns:
            List of unique strings (preserving original case)
        """
        seen: set[str] = set()
        unique: list[str] = []

        for value in values:
            if strip:
                value = value.strip()

            if not value:
                continue

            # Use lowercase for uniqueness check but preserve original case
            key = value.lower() if lowercase_key else value

            if key in seen:
                continue

            seen.add(key)
            unique.append(value)

        LOGGER.debug(
            "job_normalizer.dedupe",
            input_count=len(list(values)) if not isinstance(values, list) else len(values),
            output_count=len(unique),
        )

        return unique


__all__ = ["JobNormalizer"]
