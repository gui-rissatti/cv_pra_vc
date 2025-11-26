"""Validation helpers for scraped job data."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence
from urllib.parse import urlparse

from services.scraper import ScrapedJob

__all__ = ["ValidationIssue", "ValidationError", "JobValidator"]

_VALID_URL_SCHEMES = {"http", "https"}
_ALPHA_RE = re.compile(r"[A-Za-z]")


@dataclass(slots=True)
class ValidationIssue:
    """Represents a single validation failure."""

    layer: str
    field: str
    message: str
    code: str


class ValidationError(ValueError):
    """Raised when validation detects one or more issues."""

    def __init__(self, issues: Iterable[ValidationIssue]):
        issues_list = list(issues)
        if not issues_list:
            raise ValueError("ValidationError requires at least one issue")
        self.issues = issues_list
        summary = "; ".join(f"{issue.layer}:{issue.field}:{issue.message}" for issue in issues_list)
        super().__init__(f"Job validation failed ({summary})")


class JobValidator:
    """Runs syntax, semantic, and completeness validations over a `ScrapedJob`."""

    def __init__(
        self,
        *,
        allowed_boards: Sequence[str] | None = None,
        min_title_chars: int = 4,
        max_title_chars: int = 120,
        min_company_chars: int = 2,
        max_company_chars: int = 120,
        min_description_chars: int = 80,
        max_description_chars: int = 20000,
        min_description_words: int = 15,
        min_skill_count: int = 0,
        max_skill_count: int = 25,
    ) -> None:
        self._allowed_boards = {board.lower() for board in (allowed_boards or ["linkedin", "gupy", "indeed", "generic"])}
        self._min_title_chars = min_title_chars
        self._max_title_chars = max_title_chars
        self._min_company_chars = min_company_chars
        self._max_company_chars = max_company_chars
        self._min_description_chars = min_description_chars
        self._max_description_chars = max_description_chars
        self._min_description_words = min_description_words
        self._min_skill_count = min_skill_count
        self._max_skill_count = max_skill_count

    def validate(self, job: ScrapedJob) -> ScrapedJob:
        """Validate a scraped job, raising `ValidationError` for failures."""

        issues: list[ValidationIssue] = []
        issues.extend(self._check_syntax(job))
        issues.extend(self._check_semantics(job))
        issues.extend(self._check_completeness(job))

        if issues:
            raise ValidationError(issues)

        return self._normalize(job)

    def _check_syntax(self, job: ScrapedJob) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        parsed = urlparse(job.url)
        if parsed.scheme.lower() not in _VALID_URL_SCHEMES or not parsed.netloc:
            issues.append(self._issue("syntax", "url", "URL must include http(s) scheme and hostname", "invalid_url"))

        if not isinstance(job.title, str) or not job.title.strip():
            issues.append(self._issue("syntax", "title", "Title must be a non-empty string", "invalid_title"))

        # Company is now optional - only validate if provided
        if job.company is not None and (not isinstance(job.company, str) or not job.company.strip()):
            issues.append(self._issue("syntax", "company", "Company must be a non-empty string when provided", "invalid_company"))

        if not isinstance(job.description, str) or not job.description.strip():
            issues.append(
                self._issue("syntax", "description", "Description must be a non-empty string", "invalid_description")
            )

        if not isinstance(job.skills, list):
            issues.append(self._issue("syntax", "skills", "Skills must be a list", "invalid_skills"))
        elif any(not isinstance(skill, str) or not skill.strip() for skill in job.skills):
            issues.append(
                self._issue("syntax", "skills", "Each skill must be a non-empty string", "invalid_skill_entry")
            )

        return issues

    def _check_semantics(self, job: ScrapedJob) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        board = job.board.lower()
        if board not in self._allowed_boards:
            issues.append(self._issue("semantic", "board", f"Board '{job.board}' is not supported", "unsupported_board"))

        title = job.title.strip()
        if len(title) < self._min_title_chars or len(title) > self._max_title_chars:
            issues.append(
                self._issue(
                    "semantic",
                    "title",
                    f"Title must be between {self._min_title_chars} and {self._max_title_chars} characters",
                    "title_length_out_of_bounds",
                )
            )
        elif not _ALPHA_RE.search(title):
            issues.append(self._issue("semantic", "title", "Title must contain alphabetic characters", "title_requires_alpha"))

        # Company is optional - only validate length if provided
        if job.company is not None:
            company = job.company.strip()
            if len(company) < self._min_company_chars or len(company) > self._max_company_chars:
                issues.append(
                    self._issue(
                        "semantic",
                        "company",
                        f"Company must be between {self._min_company_chars} and {self._max_company_chars} characters",
                        "company_length_out_of_bounds",
                    )
                )

        description = job.description.strip()
        if len(description) < self._min_description_chars:
            issues.append(
                self._issue(
                    "semantic",
                    "description",
                    f"Description must contain at least {self._min_description_chars} characters",
                    "description_too_short",
                )
            )
        elif len(description) > self._max_description_chars:
            issues.append(
                self._issue(
                    "semantic",
                    "description",
                    f"Description exceeds {self._max_description_chars} characters",
                    "description_too_long",
                )
            )

        return issues

    def _check_completeness(self, job: ScrapedJob) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        description = job.description.strip()
        word_count = len(description.split())
        if word_count < self._min_description_words:
            issues.append(
                self._issue(
                    "completeness",
                    "description",
                    f"Description must contain at least {self._min_description_words} words",
                    "description_missing_detail",
                )
            )

        skills = job.skills if isinstance(job.skills, list) else []
        if len(skills) < self._min_skill_count:
            issues.append(
                self._issue(
                    "completeness",
                    "skills",
                    f"At least {self._min_skill_count} skill(s) are required",
                    "skills_missing",
                )
            )
        elif len(skills) > self._max_skill_count:
            issues.append(
                self._issue(
                    "completeness",
                    "skills",
                    f"Provide no more than {self._max_skill_count} skills",
                    "skills_excessive",
                )
            )

        return issues

    def _normalize(self, job: ScrapedJob) -> ScrapedJob:
        """Return a sanitized copy of the job for downstream layers."""

        clean_title = job.title.strip()
        clean_company = job.company.strip() if job.company is not None else None
        clean_description = job.description.strip()
        cleaned_skills = self._dedupe(skill.strip() for skill in job.skills if isinstance(skill, str))
        cleaned_skills = [skill for skill in cleaned_skills if skill]

        return ScrapedJob(
            url=job.url.strip(),
            board=job.board.lower(),
            title=clean_title,
            company=clean_company,
            description=clean_description,
            skills=cleaned_skills,
            raw_html=job.raw_html,
            company_extraction_method=job.company_extraction_method,
        )

    @staticmethod
    def _dedupe(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            key = value.lower()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(value if value[:1].isupper() else value.capitalize())
        return result

    @staticmethod
    def _issue(layer: str, field: str, message: str, code: str) -> ValidationIssue:
        return ValidationIssue(layer=layer, field=field, message=message, code=code)
