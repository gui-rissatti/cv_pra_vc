"""Endpoint for generating application materials."""

from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agents import GeneratedBundle, GenerationAgent
from core.config import get_settings
from core.llm_provider import get_llm_provider
from core.rate_limit import limiter

router = APIRouter()


class JobInput(BaseModel):
    """Job details required for generation."""

    id: str | None = None
    title: str
    company: str
    description: str
    skills: list[str]


class ProfileInput(BaseModel):
    """Candidate profile information."""

    name: str | None = None
    cv_text: str = Field(..., alias="cvText", description="Raw text content of the CV")
    language: str = Field(default="auto", description="Output language (auto, pt, en, es, fr, de)")
    tone: str = Field(default="professional", description="Tone of voice (professional, friendly, formal, enthusiastic)")
    variance: int = Field(default=3, ge=1, le=5, description="Adaptation variance level (1=strict, 5=creative)")


class GenerateRequest(BaseModel):
    """Request payload for material generation."""

    job: JobInput
    profile: ProfileInput


class GeneratedAssetsResponse(BaseModel):
    """Response payload containing generated materials."""

    job_id: str | None = Field(None, alias="jobId")
    cv: str
    cover_letter: str = Field(..., alias="coverLetter")
    networking: str
    insights: str
    match_score: int = Field(..., alias="matchScore")
    generated_at: datetime = Field(..., alias="generatedAt")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: list[str] | None = None


@lru_cache(maxsize=1)
def _generation_agent_singleton() -> GenerationAgent:
    llm_provider = get_llm_provider("gemini")
    return GenerationAgent(llm_provider=llm_provider)


def get_generation_agent() -> GenerationAgent:
    """Dependency provider for GenerationAgent."""
    return _generation_agent_singleton()


@router.post(
    "/generate-materials",
    response_model=GeneratedAssetsResponse,
    summary="Generate application materials",
    tags=["generation"],
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse},
    },
)
@limiter.limit(get_settings().rate_limit_generation)
async def generate_materials(
    request: Request,
    payload: GenerateRequest = Body(...),
    agent: GenerationAgent = Depends(get_generation_agent),
) -> GeneratedAssetsResponse:
    """Generate CV, cover letter, and insights based on job and profile."""
    
    try:
        # Convert Pydantic model to dict for the agent
        job_data = payload.job.model_dump()
        
        result: GeneratedBundle = await agent.generate_all(
            job_data=job_data,
            cv_text=payload.profile.cv_text,
            language=payload.profile.language,
            tone=payload.profile.tone,
            variance=payload.profile.variance,
        )
        
        return GeneratedAssetsResponse(
            jobId=payload.job.id,
            cv=result.cv,
            coverLetter=result.cover_letter,
            networking=result.networking,
            insights=result.insights,
            matchScore=result.match_score,
            generatedAt=result.generated_at,
        )
        
    except Exception as exc:
        # In a real app, we'd handle specific agent errors (e.g. context length exceeded)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="generation_failed",
                message=str(exc),
            ).model_dump(exclude_none=True),
        )
