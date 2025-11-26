"""Web scraping utilities for supported job boards."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable
from urllib.parse import urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

from services.company_fallback import CompanyNameFallbackService


LOGGER = structlog.get_logger(__name__)


__all__ = [
    "ScrapedJob",
    "ScraperError",
    "FetchError",
    "ParseError",
    "UnsupportedJobBoardError",
    "WebScraperService",
]


@dataclass(slots=True)
class ScrapedJob:
    """Structured representation of a scraped job posting."""

    url: str
    board: str
    title: str
    company: str | None
    description: str
    skills: list[str]
    raw_html: str
    company_extraction_method: str | None = None


class ScraperError(RuntimeError):
    """Base exception for scraper failures."""


class UnsupportedJobBoardError(ScraperError):
    """Raised when the provided URL does not match a supported domain."""


class FetchError(ScraperError):
    """Raised when the remote page cannot be retrieved successfully."""


class ParseError(ScraperError):
    """Raised when the fetched page is missing required fields."""


class WebScraperService:
    """Scrape job postings from supported job boards using HTTPX + BeautifulSoup."""

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 15.0,
        company_fallback: CompanyNameFallbackService | None = None,
    ) -> None:
        self._client = client
        self._timeout = timeout
        self._company_fallback = company_fallback or CompanyNameFallbackService()
        self._parsers: dict[str, Callable[[str, str, str], ScrapedJob]] = {
            "linkedin": self._parse_linkedin,
            "gupy": self._parse_gupy,
            "indeed": self._parse_indeed,
            "generic": self._parse_generic,
        }

    async def fetch_job(self, url: str) -> ScrapedJob:
        """Download and parse the job posting for the given URL."""

        board = self._resolve_board(url)
        html = await self._download(url)
        parser = self._parsers[board]
        return parser(url, html, board)

    def _resolve_board(self, url: str) -> str:
        netloc = urlparse(url).netloc.lower()
        if "linkedin" in netloc:
            return "linkedin"
        if "gupy" in netloc:
            return "gupy"
        if "indeed" in netloc:
            return "indeed"
        return "generic"

    async def _download(self, url: str) -> str:
        client = self._client
        owns_client = False
        if client is None:
            # Use a browser-like User-Agent to avoid being blocked by some sites
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            client = httpx.AsyncClient(follow_redirects=True, headers=headers)
            owns_client = True
        try:
            response = await client.get(url, timeout=self._timeout)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as exc:  # pragma: no cover - relies on HTTPX behavior
            raise FetchError(f"Failed to fetch '{url}'") from exc
        finally:
            if owns_client:
                await client.aclose()

    def _parse_linkedin(self, url: str, html: str, board: str) -> ScrapedJob:
        soup = BeautifulSoup(html, "html.parser")
        title = self._first_text(
            soup,
            [
                "h1.top-card-layout__title",
                "h1[data-test-job-title]",
                "h1",
            ],
        )
        company = self._first_text(
            soup,
            [
                "a.topcard__org-name-link",
                "span.topcard__flavor",
                "div.topcard__flavor",
            ],
        )
        description = self._description(
            soup,
            [
                "div.description__text",
                "div[data-test-description]",
                "section[data-view-name='job-details']",
            ],
        )
        skills = self._skills(
            soup,
            [
                "li.description__job-criteria-item",
                "li.skills-requirements__item",
            ],
        )
        return self._build_result(url, board, title, company, description, skills, html)

    def _parse_gupy(self, url: str, html: str, board: str) -> ScrapedJob:
        soup = BeautifulSoup(html, "html.parser")
        title = self._first_text(soup, ["h1.job-header__title", "h1"])
        company = self._first_text(soup, ["span.job-header__company", "span[data-testid='company-name']"])
        description = self._description(
            soup,
            [
                "section#job-description",
                "div[data-testid='job-description']",
            ],
        )
        skills = self._skills(soup, ["ul.job-requirements__list li", "li[data-testid='requirement-item']"])
        return self._build_result(url, board, title, company, description, skills, html)

    def _parse_indeed(self, url: str, html: str, board: str) -> ScrapedJob:
        soup = BeautifulSoup(html, "html.parser")
        title = self._first_text(soup, ["h1.jobsearch-JobInfoHeader-title", "h1"])
        company = self._first_text(
            soup,
            [
                "div.jobsearch-InlineCompanyRating",
                "div[data-company-name]",
            ],
        )
        description = self._description(
            soup,
            [
                "div#jobDescriptionText",
                "div.jobsearch-JobComponent-description",
            ],
        )
        skills = self._skills(
            soup,
            [
                "div.jobsearch-ReqAndQualSection-item",
                "li.jobsearch-ReqAndQualSection-item",
            ],
        )
        return self._build_result(url, board, title, company, description, skills, html)

    def _build_result(
        self,
        url: str,
        board: str,
        title: str | None,
        company: str | None,
        description: str | None,
        skills: list[str],
        raw_html: str,
    ) -> ScrapedJob:
        if not title:
            raise ParseError("Job title not found in document")
        if not description:
            raise ParseError("Job description not found in document")

        # Apply fallback strategies for company name
        company_result = self._company_fallback.extract_company(
            scraped_company=company,
            html=raw_html,
            url=url,
            description=description,
        )

        LOGGER.info(
            "scraper.company_extraction",
            url=url[:100],
            method=company_result.method,
            confidence=company_result.confidence,
            found=bool(company_result.company),
        )

        return ScrapedJob(
            url=url,
            board=board,
            title=title,
            company=company_result.company,
            description=description,
            skills=skills,
            raw_html=raw_html,
            company_extraction_method=f"{company_result.method}:{company_result.confidence}",
        )

    def _first_text(self, soup: BeautifulSoup, selectors: Iterable[str]) -> str | None:
        for selector in selectors:
            node = soup.select_one(selector)
            if not node:
                continue
            text = node.get_text(" ", strip=True)
            if text:
                return text
        return None

    def _description(self, soup: BeautifulSoup, selectors: Iterable[str]) -> str | None:
        chunks: list[str] = []
        for selector in selectors:
            nodes = soup.select(selector)
            if not nodes:
                continue
            for node in nodes:
                text = node.get_text(" ", strip=True)
                if text:
                    chunks.append(text)
            if chunks:
                break
        if not chunks and soup.body:
            text = soup.body.get_text(" ", strip=True)
            if text:
                chunks.append(text)
        return "\n".join(chunks) if chunks else None

    def _skills(self, soup: BeautifulSoup, selectors: Iterable[str]) -> list[str]:
        values: list[str] = []
        for selector in selectors:
            nodes = soup.select(selector)
            for node in nodes:
                text = node.get_text(" ", strip=True)
                if text:
                    values.append(text)
        return self._dedupe(values)

    def _dedupe(self, values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(value)
        return unique

    def _parse_generic(self, url: str, html: str, board: str) -> ScrapedJob:
        """Fallback parser for unsupported domains."""
        soup = BeautifulSoup(html, "html.parser")

        # Try to find title
        title = "Unknown Position"
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        # Try to find company
        company = "Unknown Company"
        og_site_name = soup.find("meta", property="og:site_name")
        if og_site_name:
            company = str(og_site_name.get("content", "Unknown Company"))

        # Description: try to find the main content
        description = ""
        # Common content containers
        main_content = (
            soup.find("main") 
            or soup.find("article") 
            or soup.find("div", {"id": "content"}) 
            or soup.find("div", {"class": "content"}) 
            or soup.body
        )
        
        if main_content:
            # Remove noise
            for tag in main_content(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                tag.decompose()
            description = main_content.get_text("\n", strip=True)

        return ScrapedJob(
            url=url,
            board=board,
            title=title,
            company=company,
            description=description,
            skills=[],
            raw_html=html[:10000],  # Keep enough context
        )
