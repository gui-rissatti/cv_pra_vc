"""LLM-powered extraction agent that normalizes scraped job content."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from textwrap import shorten
from typing import Iterable

import structlog
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from core.llm_provider import LLMProvider, get_llm_provider
from core.validators import JobValidator, ValidationError
from services.scraper import ScrapedJob


LOGGER = structlog.get_logger(__name__)


@dataclass(slots=True)
class ExtractionAgentResult:
    """Represents the structured output coming from the LLM pipeline."""

    job: ScrapedJob
    highlights: list[str]


class _StructuredJobPayload(BaseModel):
    title: str = Field(..., description="Canonical job title")
    company: str = Field(..., description="Canonical employer name")
    description: str = Field(..., description="Concise but detailed responsibilities and requirements")
    skills: list[str] = Field(default_factory=list, description="Sorted, deduplicated skills")
    highlights: list[str] = Field(default_factory=list, description="Key bullet points extracted from the posting")


class ExtractionAgentError(RuntimeError):
    """Raised when the extraction agent cannot produce a structured job."""


class ExtractionAgent:
    """Pipeline that feeds scraped HTML/content into an LLM for extraction."""

    def __init__(
        self,
        *,
        llm_provider: LLMProvider | None = None,
        validator: JobValidator | None = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        highlight_count: int = 3,
    ) -> None:
        """
        Initialize ExtractionAgent.

        Args:
            llm_provider: LLM provider instance. If None, creates default Gemini provider.
            validator: Job validator instance. If None, creates default validator.
            model: Model name (used if creating default provider)
            temperature: Temperature for LLM generation
            highlight_count: Number of highlights to extract
        """
        self._validator = validator or JobValidator()
        self._highlight_count = highlight_count
        self._parser = PydanticOutputParser(pydantic_object=_StructuredJobPayload)
        self._prompt_template = self._build_prompt()
        self._llm_provider = llm_provider or get_llm_provider("gemini", model=model)
        self._temperature = temperature

    async def run(self, scraped_job: ScrapedJob) -> ExtractionAgentResult:
        """Normalize a scraped job using the LLM and return merged results."""

        LOGGER.debug("extraction_agent.run.start", board=scraped_job.board, url=scraped_job.url)
        validated = self._validated(scraped_job)
        prompt_text = self._build_prompt_text(validated)

        try:
            # Call LLM provider to get structured output
            llm_response = await self._llm_provider.generate(
                prompt_text,
                temperature=self._temperature,
            )
            # Parse the LLM response into structured format
            structured = self._parser.parse(llm_response)
        except Exception as exc:
            LOGGER.error("extraction_agent.run.failed", error=str(exc))
            raise ExtractionAgentError("LLM extraction failed") from exc

        merged_job = self._merge_payload(validated, structured)
        final_job = self._validated(merged_job)
        LOGGER.debug("extraction_agent.run.success", board=final_job.board, url=final_job.url)
        return ExtractionAgentResult(job=final_job, highlights=structured.highlights)

    def _validated(self, job: ScrapedJob) -> ScrapedJob:
        try:
            return self._validator.validate(job)
        except ValidationError as exc:
            # Provide detailed validation issues to help diagnose problems
            error_details = "\n".join(f"  - {issue.field}: {issue.message}" for issue in exc.issues)
            raise ExtractionAgentError(f"Validation failed for scraped job:\n{error_details}") from exc

    def _merge_payload(self, original: ScrapedJob, structured: _StructuredJobPayload) -> ScrapedJob:
        skills = structured.skills or original.skills
        deduped_skills = self._dedupe(skills)
        return ScrapedJob(
            url=original.url,
            board=original.board,
            title=structured.title or original.title,
            company=structured.company or original.company,
            description=structured.description or original.description,
            skills=deduped_skills,
            raw_html=original.raw_html,
        )

    def _build_prompt(self) -> ChatPromptTemplate:
        """Build the LangChain ChatPromptTemplate."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert technical recruiter. Transform scraped job postings into a structured, "
                    "clean summary with consistent casing and deduplicated skills. Only use the provided "
                    "content; never invent employers or titles. Return JSON that matches the provided format instructions.",
                ),
                (
                    "human",
                    "Job data: {job_data}\n\nHTML snippet:\n{job_html_preview}\n\n"
                    "You must respond with JSON using the following schema instructions:\n{format_instructions}\n"
                    "Generate up to {highlight_count} concise highlights describing the opportunity.",
                ),
            ]
        )

    def _build_prompt_text(self, job: ScrapedJob) -> str:
        """Build the full prompt text for LLM."""
        job_dict = asdict(job)
        format_instructions = self._parser.get_format_instructions()
        html_preview = self._html_preview(job.raw_html)

        system_msg = (
            "You are an expert technical recruiter. Transform scraped job postings into a structured, "
            "clean summary with consistent casing and deduplicated skills. Only use the provided "
            "content; never invent employers or titles. Return JSON that matches the provided format instructions."
        )

        human_msg = (
            f"Job data: {job_dict}\n\nHTML snippet:\n{html_preview}\n\n"
            f"You must respond with JSON using the following schema instructions:\n{format_instructions}\n"
            f"Generate up to {self._highlight_count} concise highlights describing the opportunity."
        )

        return f"{system_msg}\n\n{human_msg}"

    @staticmethod
    def _html_preview(html: str, limit: int = 2000) -> str:
        return shorten(html, width=limit, placeholder=" …") if html else ""

    @staticmethod
    def _dedupe(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            normalized = value.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        return unique


__all__ = ["ExtractionAgent", "ExtractionAgentError", "ExtractionAgentResult"]
