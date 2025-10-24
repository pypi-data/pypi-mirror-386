"""
Pydantic models for the SmartScraper API endpoint.

This module defines request and response models for the SmartScraper endpoint,
which performs AI-powered web scraping with optional pagination and scrolling support.

The SmartScraper can:
- Extract structured data from websites based on user prompts
- Handle infinite scroll scenarios
- Support pagination across multiple pages
- Accept custom output schemas for structured extraction
- Process either URLs or raw HTML content
"""

from typing import Dict, Optional, Type
from uuid import UUID

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, conint, model_validator


class SmartScraperRequest(BaseModel):
    """
    Request model for the SmartScraper endpoint.

    This model validates and structures requests for AI-powered web scraping.
    You must provide either website_url or website_html (but not both).

    Attributes:
        user_prompt: Natural language prompt describing what to extract
        website_url: URL of the website to scrape (optional)
        website_html: Raw HTML content to scrape (optional, max 2MB)
        headers: Optional HTTP headers including cookies
        cookies: Optional cookies for authentication/session management
        output_schema: Optional Pydantic model defining the output structure
        number_of_scrolls: Number of times to scroll (0-100) for infinite scroll pages
        total_pages: Number of pages to scrape (1-10) for pagination
        mock: Whether to use mock mode for testing
        plain_text: Whether to return plain text instead of structured data
        render_heavy_js: Whether to render heavy JavaScript content

    Example:
        >>> request = SmartScraperRequest(
        ...     website_url="https://example.com",
        ...     user_prompt="Extract all product names and prices"
        ... )
    """
    user_prompt: str = Field(
        ...,
        example="Extract info about the company",
    )
    website_url: Optional[str] = Field(
        default=None, example="https://scrapegraphai.com/"
    )
    website_html: Optional[str] = Field(
        default=None,
        example="<html><body><h1>Title</h1><p>Content</p></body></html>",
        description="HTML content, maximum size 2MB",
    )
    headers: Optional[dict[str, str]] = Field(
        None,
        example={
            "User-Agent": "scrapegraph-py",
            "Cookie": "cookie1=value1; cookie2=value2",
        },
        description="Optional headers to send with the request, including cookies "
        "and user agent",
    )
    cookies: Optional[Dict[str, str]] = Field(
        None,
        example={"session_id": "abc123", "user_token": "xyz789"},
        description="Dictionary of cookies to send with the request for "
        "authentication or session management",
    )
    output_schema: Optional[Type[BaseModel]] = None
    number_of_scrolls: Optional[conint(ge=0, le=100)] = Field(
        default=None,
        description="Number of times to scroll the page (0-100). If None, no "
        "scrolling will be performed.",
        example=10,
    )
    total_pages: Optional[conint(ge=1, le=10)] = Field(
        default=None,
        description="Number of pages to scrape (1-10). If None, only the first "
        "page will be scraped.",
        example=5,
    )
    mock: bool = Field(default=False, description="Whether to use mock mode for the request")
    plain_text: bool = Field(default=False, description="Whether to return the result as plain text")
    render_heavy_js: bool = Field(default=False, description="Whether to render heavy JavaScript on the page")
    stealth: bool = Field(default=False, description="Enable stealth mode to avoid bot detection")

    @model_validator(mode="after")
    def validate_user_prompt(self) -> "SmartScraperRequest":
        if self.user_prompt is None or not self.user_prompt.strip():
            raise ValueError("User prompt cannot be empty")
        if not any(c.isalnum() for c in self.user_prompt):
            raise ValueError("User prompt must contain a valid prompt")
        return self

    @model_validator(mode="after")
    def validate_url_and_html(self) -> "SmartScraperRequest":
        if self.website_html is not None:
            if len(self.website_html.encode("utf-8")) > 2 * 1024 * 1024:
                raise ValueError("Website HTML content exceeds maximum size of 2MB")
            try:
                soup = BeautifulSoup(self.website_html, "html.parser")
                if not soup.find():
                    raise ValueError("Invalid HTML - no parseable content found")
            except Exception as e:
                raise ValueError(f"Invalid HTML structure: {str(e)}")
        elif self.website_url is not None:
            if not self.website_url.strip():
                raise ValueError("Website URL cannot be empty")
            if not (
                self.website_url.startswith("http://")
                or self.website_url.startswith("https://")
            ):
                raise ValueError("Invalid URL")
        else:
            raise ValueError("Either website_url or website_html must be provided")
        return self

    def model_dump(self, *args, **kwargs) -> dict:
        # Set exclude_none=True to exclude None values from serialization
        kwargs.setdefault("exclude_none", True)
        data = super().model_dump(*args, **kwargs)
        # Convert the Pydantic model schema to dict if present
        if self.output_schema is not None:
            data["output_schema"] = self.output_schema.model_json_schema()
        return data


class GetSmartScraperRequest(BaseModel):
    """Request model for get_smartscraper endpoint"""

    request_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

    @model_validator(mode="after")
    def validate_request_id(self) -> "GetSmartScraperRequest":
        try:
            # Validate the request_id is a valid UUID
            UUID(self.request_id)
        except ValueError:
            raise ValueError("request_id must be a valid UUID")
        return self
