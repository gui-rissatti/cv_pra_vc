"""Endpoint for extracting structured job details from a vacancy URL."""

from datetime import datetime, timezone
from functools import lru_cache
import hashlib
from typing import Iterable

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from agents import ExtractionAgent, ExtractionAgentError
from core.config import get_settings
from core.llm_provider import get_llm_provider
from core.rate_limit import limiter
from core.validators import ValidationError as JobValidationError
from services.scraper import (
    ParseError,
    ScraperError,
    ScrapedJob,
    UnsupportedJobBoardError,
    WebScraperService,
)

router = APIRouter()


class ExtractJobDetailsRequest(BaseModel):
    """Inbound payload containing the job posting URL."""

    url: AnyHttpUrl = Field(..., description="Job posting URL to scrape and normalize")


class JobResponse(BaseModel):
    """Normalized job payload that satisfies the public contract."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Stable identifier derived from the job URL", example="9a1b2c3d4e5f")
    url: AnyHttpUrl = Field(..., description="Original job posting URL")
    title: str = Field(..., description="Canonical job title after normalization")
    company: str = Field(..., description="Employer name extracted from the posting")
    description: str = Field(..., description="Detailed description of the opportunity")
    skills: list[str] = Field(default_factory=list, description="Distinct list of skills mentioned")
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        description="Timestamp of when the job was processed",
        example="2025-11-19T10:00:00Z",
    )


class ErrorResponse(BaseModel):
    """Shared error response schema for the extraction endpoint."""

    error: str
    message: str
    details: list[str] | None = None


@lru_cache(maxsize=1)
def _scraper_singleton() -> WebScraperService:
    return WebScraperService()


@lru_cache(maxsize=1)
def _extraction_agent_singleton() -> ExtractionAgent:
    llm_provider = get_llm_provider("gemini")
    return ExtractionAgent(llm_provider=llm_provider)


def get_scraper_service() -> WebScraperService:
    """Provide a reusable scraper instance; overridable in tests."""

    return _scraper_singleton()


def get_extraction_agent() -> ExtractionAgent:
    """Provide the extraction agent dependency."""

    return _extraction_agent_singleton()


def _error_response(status_code: int, *, error: str, message: str, details: Iterable[str] | None = None) -> JSONResponse:
    payload = ErrorResponse(
        error=error,
        message=message,
        details=list(details) if details else None,
    ).model_dump(exclude_none=True)
    return JSONResponse(status_code=status_code, content=payload)


def _job_identifier(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def _job_response(job: ScrapedJob) -> JobResponse:
    return JobResponse(
        id=_job_identifier(job.url),
        url=job.url,
        title=job.title,
        company=job.company,
        description=job.description,
        skills=list(job.skills),
        created_at=datetime.now(timezone.utc),
    )


def _validation_details(exc: BaseException | None) -> list[str] | None:
    if isinstance(exc, JobValidationError):  # pragma: no cover - exercised via agent tests
        return [f"{issue.layer}.{issue.field}: {issue.message}" for issue in exc.issues]
    return None


@router.post(
    "/extract-job-details",
    response_model=JobResponse,
    summary="Extract job information from a provided URL",
    tags=["extraction"],
    responses={
        400: {"model": ErrorResponse, "description": "The supplied URL is unsupported or malformed."},
        422: {
            "model": ErrorResponse,
            "description": "Scraping succeeded but essential fields are missing or invalid.",
        },
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Unexpected error while scraping or processing the job."},
    },
)
@limiter.limit(get_settings().rate_limit_extraction)
async def extract_job_details(
    request: Request,
    payload: ExtractJobDetailsRequest = Body(...),
    scraper: WebScraperService = Depends(get_scraper_service),
    agent: ExtractionAgent = Depends(get_extraction_agent),
) -> JobResponse:
    """Scrape a job posting and return a normalized payload that matches the Job schema."""

    try:
        scraped = await scraper.fetch_job(str(payload.url))
    except UnsupportedJobBoardError as exc:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error="unsupported_url",
            message=str(exc),
        )
    except ParseError as exc:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="scrape_parse_error",
            message=str(exc),
        )
    except ScraperError as exc:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="scrape_failed",
            message=str(exc),
        )

    try:
        agent_result = await agent.run(scraped)
    except ExtractionAgentError as exc:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="extraction_failed",
            message=str(exc),
            details=_validation_details(exc.__cause__),
        )

    return _job_response(agent_result.job)
