"""Fallback strategies for extracting company name from job postings."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

import structlog
from bs4 import BeautifulSoup


LOGGER = structlog.get_logger(__name__)


@dataclass(slots=True)
class CompanyExtractionResult:
    """Result of company name extraction with metadata."""

    company: str | None
    method: Literal["scraper", "email", "context", "url", "meta_tag", "domain", "not_found"]
    confidence: Literal["high", "medium", "low"]


class CompanyNameFallbackService:
    """Service that applies multiple fallback strategies to extract company name."""

    # Common domain patterns to remove
    DOMAIN_SUFFIXES = [
        ".com", ".com.br", ".br", ".io", ".ai", ".tech", ".net", ".org",
        ".app", ".dev", ".co", ".jobs", ".careers", ".work"
    ]

    # Common job board domains to ignore
    JOB_BOARDS = [
        "linkedin", "gupy", "indeed", "glassdoor", "vagas", "catho",
        "infojobs", "trampos", "99jobs", "recruiter", "workable"
    ]

    def extract_company(
        self,
        *,
        scraped_company: str | None = None,
        html: str = "",
        url: str = "",
        description: str = "",
    ) -> CompanyExtractionResult:
        """
        Extract company name using multiple fallback strategies.

        Tries methods in order of confidence:
        1. Use scraped company if available (high confidence)
        2. Extract from email addresses (medium confidence)
        3. Find in context patterns (medium confidence)
        4. Extract from URL (low confidence)
        5. Find in meta tags (medium confidence)
        6. Extract from domain (low confidence)

        Args:
            scraped_company: Company name from scraper if available
            html: Raw HTML content
            url: Job posting URL
            description: Job description text

        Returns:
            CompanyExtractionResult with company name, method used, and confidence
        """
        LOGGER.debug("company_fallback.start", has_scraped=bool(scraped_company))

        # Strategy 1: Use scraped company (highest confidence)
        if scraped_company and scraped_company.strip():
            cleaned = self._clean_company_name(scraped_company)
            if cleaned and cleaned.lower() not in ["unknown company", "unknown"]:
                LOGGER.info("company_fallback.success", method="scraper", company=cleaned)
                return CompanyExtractionResult(
                    company=cleaned,
                    method="scraper",
                    confidence="high"
                )

        soup = BeautifulSoup(html, "html.parser") if html else None

        # Strategy 2: Extract from email addresses (medium confidence)
        result = self._extract_from_email(description, html)
        if result.company:
            LOGGER.info("company_fallback.success", method="email", company=result.company)
            return result

        # Strategy 3: Find in context patterns (medium confidence)
        result = self._extract_from_context(description)
        if result.company:
            LOGGER.info("company_fallback.success", method="context", company=result.company)
            return result

        # Strategy 4: Extract from meta tags (medium confidence)
        if soup:
            result = self._extract_from_meta_tags(soup)
            if result.company:
                LOGGER.info("company_fallback.success", method="meta_tag", company=result.company)
                return result

        # Strategy 5: Extract from URL (low confidence)
        result = self._extract_from_url(url)
        if result.company:
            LOGGER.info("company_fallback.success", method="url", company=result.company)
            return result

        # Strategy 6: Extract from domain (low confidence)
        result = self._extract_from_domain(url)
        if result.company:
            LOGGER.info("company_fallback.success", method="domain", company=result.company)
            return result

        LOGGER.warning("company_fallback.not_found", url=url[:100])
        return CompanyExtractionResult(
            company=None,
            method="not_found",
            confidence="low"
        )

    def _extract_from_email(self, description: str, html: str) -> CompanyExtractionResult:
        """Extract company from email addresses like rh@empresa.com -> Empresa."""
        text = f"{description} {html}"

        # Regex for email addresses
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})\b'
        matches = re.findall(email_pattern, text, re.IGNORECASE)

        for domain in matches:
            # Remove common job board domains
            if any(board in domain.lower() for board in self.JOB_BOARDS):
                continue

            # Extract company from domain
            parts = domain.split('.')
            if parts:
                company_candidate = parts[0]
                cleaned = self._clean_company_name(company_candidate)
                if cleaned and len(cleaned) > 2:
                    return CompanyExtractionResult(
                        company=cleaned.title(),
                        method="email",
                        confidence="medium"
                    )

        return CompanyExtractionResult(company=None, method="email", confidence="low")

    def _extract_from_context(self, description: str) -> CompanyExtractionResult:
        """Extract company from context patterns like 'na empresa X' or 'About X'."""
        if not description:
            return CompanyExtractionResult(company=None, method="context", confidence="low")

        # Portuguese patterns
        patterns = [
            r'(?:na|da|pela|para a?)\s+(?:empresa\s+)?([A-Z][A-Za-z0-9\s&.-]{2,30})',
            r'(?:Sobre a|A)\s+([A-Z][A-Za-z0-9\s&.-]{2,30})\s+é uma',
            r'(?:Trabalhe na|Venha para a?)\s+([A-Z][A-Za-z0-9\s&.-]{2,30})',
            # English patterns
            r'(?:at|with|for)\s+([A-Z][A-Za-z0-9\s&.-]{2,30})\s+(?:we|is|are)',
            r'(?:About|Join)\s+([A-Z][A-Za-z0-9\s&.-]{2,30})',
            r'([A-Z][A-Za-z0-9\s&.-]{2,30})\s+is\s+(?:hiring|looking|seeking)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                cleaned = self._clean_company_name(match)
                if cleaned and len(cleaned) > 2:
                    # Validate it doesn't look like a job title
                    if not any(word in cleaned.lower() for word in [
                        "developer", "engineer", "designer", "manager", "analyst",
                        "desenvolvedor", "engenheiro", "analista", "gerente"
                    ]):
                        return CompanyExtractionResult(
                            company=cleaned,
                            method="context",
                            confidence="medium"
                        )

        return CompanyExtractionResult(company=None, method="context", confidence="low")

    def _extract_from_url(self, url: str) -> CompanyExtractionResult:
        """Extract company from URL path segments."""
        if not url:
            return CompanyExtractionResult(company=None, method="url", confidence="low")

        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        # Look for company in path (e.g., /company/acme/jobs)
        for i, part in enumerate(path_parts):
            if part.lower() in ['company', 'companies', 'empresa', 'empresas']:
                if i + 1 < len(path_parts):
                    company_candidate = path_parts[i + 1]
                    cleaned = self._clean_company_name(company_candidate)
                    if cleaned and len(cleaned) > 2:
                        return CompanyExtractionResult(
                            company=cleaned.title(),
                            method="url",
                            confidence="low"
                        )

        return CompanyExtractionResult(company=None, method="url", confidence="low")

    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> CompanyExtractionResult:
        """Extract company from HTML meta tags."""
        # Try various meta tags
        meta_patterns = [
            ("property", "og:site_name"),
            ("name", "author"),
            ("name", "application-name"),
            ("property", "al:android:app_name"),
            ("property", "al:ios:app_name"),
        ]

        for attr, value in meta_patterns:
            meta = soup.find("meta", {attr: value})
            if meta:
                content = meta.get("content", "")
                if content and isinstance(content, str):
                    cleaned = self._clean_company_name(content)
                    # Filter out generic names
                    if cleaned and len(cleaned) > 2 and not any(
                        board in cleaned.lower() for board in self.JOB_BOARDS
                    ):
                        return CompanyExtractionResult(
                            company=cleaned,
                            method="meta_tag",
                            confidence="medium"
                        )

        return CompanyExtractionResult(company=None, method="meta_tag", confidence="low")

    def _extract_from_domain(self, url: str) -> CompanyExtractionResult:
        """Extract company from domain name as last resort."""
        if not url:
            return CompanyExtractionResult(company=None, method="domain", confidence="low")

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]

        # Skip if it's a known job board
        if any(board in domain for board in self.JOB_BOARDS):
            return CompanyExtractionResult(company=None, method="domain", confidence="low")

        # Extract main domain part
        parts = domain.split('.')
        if parts:
            company_candidate = parts[0]
            cleaned = self._clean_company_name(company_candidate)
            if cleaned and len(cleaned) > 2:
                return CompanyExtractionResult(
                    company=cleaned.title(),
                    method="domain",
                    confidence="low"
                )

        return CompanyExtractionResult(company=None, method="domain", confidence="low")

    def _clean_company_name(self, name: str) -> str:
        """Clean and normalize company name."""
        if not name:
            return ""

        # Remove URL encoding and special chars
        cleaned = name.strip()
        cleaned = re.sub(r'[_-]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()

        # Remove common suffixes if found
        for suffix in self.DOMAIN_SUFFIXES:
            if cleaned.lower().endswith(suffix):
                cleaned = cleaned[:len(cleaned) - len(suffix)]

        # Capitalize properly
        cleaned = cleaned.strip()
        if cleaned:
            # If all caps, convert to title case
            if cleaned.isupper() and len(cleaned) > 3:
                cleaned = cleaned.title()

        return cleaned


__all__ = ["CompanyNameFallbackService", "CompanyExtractionResult"]
