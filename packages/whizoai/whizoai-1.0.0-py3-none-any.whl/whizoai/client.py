"""
WhizoAI SDK Client
"""

import os
import time
from typing import Optional, Dict, Any, List
import requests

from .exceptions import (
    WhizoAIError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    NetworkError,
)


class WhizoAI:
    """
    WhizoAI API client

    Args:
        api_key: Your WhizoAI API key (or set WHIZOAI_API_KEY environment variable)
        api_url: API base URL (default: https://api.whizo.ai)
        timeout: Request timeout in seconds (default: 30)
        retry_attempts: Number of retry attempts (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1)

    Example:
        ```python
        from whizoai import WhizoAI

        client = WhizoAI(api_key="whizo_your_api_key_here")
        result = client.scrape("https://example.com")
        print(result["data"]["content"])
        ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = "https://api.whizo.ai",
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: int = 1,
    ):
        self.api_key = api_key or os.getenv("WHIZOAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Get one at https://whizo.ai/app/api-keys"
            )

        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "WhizoAI-Python-SDK/1.0.0",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API request with retry logic"""
        url = f"{self.api_url}{endpoint}"

        for attempt in range(1, self.retry_attempts + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.timeout,
                )

                # Handle HTTP errors
                if response.status_code >= 400:
                    error_data = response.json() if response.text else {}
                    message = (
                        error_data.get("error", {}).get("message")
                        or error_data.get("message")
                        or response.text
                    )

                    if response.status_code == 401:
                        raise AuthenticationError(message)
                    elif response.status_code == 402:
                        raise InsufficientCreditsError(message)
                    elif response.status_code == 429:
                        raise RateLimitError(message)
                    else:
                        raise WhizoAIError(
                            message,
                            error_data.get("error", {}).get("code"),
                            response.status_code,
                            error_data.get("error", {}).get("details"),
                        )

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt >= self.retry_attempts:
                    raise NetworkError(str(e))

                # Exponential backoff
                delay = self.retry_delay * (2 ** (attempt - 1))
                time.sleep(delay)

        raise NetworkError("Max retry attempts exceeded")

    # =========================================================================
    # Scraping Methods
    # =========================================================================

    def scrape(
        self,
        url: str,
        format: str = "markdown",
        include_screenshot: bool = False,
        include_pdf: bool = False,
        wait_for: Optional[int] = None,
        timeout: Optional[int] = None,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        only_main_content: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Scrape a single webpage

        Args:
            url: The URL to scrape
            format: Output format ('markdown', 'html', 'text', 'json')
            include_screenshot: Capture a screenshot (+1 credit)
            include_pdf: Generate a PDF (+1 credit)
            wait_for: Milliseconds to wait before scraping
            timeout: Request timeout in milliseconds
            include_tags: HTML tags to include
            exclude_tags: HTML tags to exclude
            only_main_content: Extract only main content

        Returns:
            Dictionary containing scraped data and metadata

        Example:
            ```python
            result = client.scrape("https://example.com", format="markdown")
            print(result["data"]["content"])
            ```
        """
        data = {
            "url": url,
            "format": format,
            "includeScreenshot": include_screenshot,
            "includePdf": include_pdf,
            "onlyMainContent": only_main_content,
            **kwargs,
        }

        if wait_for is not None:
            data["waitFor"] = wait_for
        if timeout is not None:
            data["timeout"] = timeout
        if include_tags:
            data["includeTags"] = include_tags
        if exclude_tags:
            data["excludeTags"] = exclude_tags

        return self._request("POST", "/v1/scrape", data=data)

    def crawl(
        self,
        url: str,
        max_depth: int = 3,
        max_pages: int = 100,
        format: str = "markdown",
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Crawl multiple pages of a website

        Args:
            url: Starting URL to crawl from
            max_depth: Maximum crawl depth (1-10)
            max_pages: Maximum number of pages to crawl
            format: Output format for each page
            include_paths: URL patterns to include
            exclude_paths: URL patterns to exclude

        Returns:
            Dictionary containing job ID or crawl results
        """
        data = {
            "url": url,
            "maxDepth": max_depth,
            "maxPages": max_pages,
            "format": format,
            **kwargs,
        }

        if include_paths:
            data["includePaths"] = include_paths
        if exclude_paths:
            data["excludePaths"] = exclude_paths

        return self._request("POST", "/v1/crawl", data=data)

    def extract(
        self,
        url: str,
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Extract structured data from a webpage using AI

        Args:
            url: The URL to extract data from
            schema: JSON schema defining structure to extract
            prompt: Natural language prompt for extraction
            model: AI model to use ('gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo')
            system_prompt: Custom system prompt

        Returns:
            Dictionary containing extracted structured data
        """
        data = {"url": url, "model": model, **kwargs}

        if schema:
            data["schema"] = schema
        if prompt:
            data["prompt"] = prompt
        if system_prompt:
            data["systemPrompt"] = system_prompt

        return self._request("POST", "/v1/extract", data=data)

    def search(
        self,
        query: str,
        max_results: int = 10,
        scrape_results: bool = False,
        country: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Search the web and optionally scrape results

        Args:
            query: Search query
            max_results: Maximum number of results (1-20)
            scrape_results: Whether to scrape full content from each result
            country: Country code for localized results
            language: Language code for results

        Returns:
            Dictionary containing search results
        """
        data = {
            "query": query,
            "maxResults": max_results,
            "scrapeResults": scrape_results,
            **kwargs,
        }

        if country:
            data["country"] = country
        if language:
            data["language"] = language

        return self._request("POST", "/v1/search", data=data)

    def map(
        self,
        url: str,
        max_depth: int = 2,
        max_pages: int = 100,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Discover all URLs on a website without scraping content

        Args:
            url: Starting URL
            max_depth: Maximum depth to crawl (1-5)
            max_pages: Maximum pages to discover
            include_paths: URL patterns to include
            exclude_paths: URL patterns to exclude

        Returns:
            Dictionary containing discovered URLs
        """
        data = {"url": url, "maxDepth": max_depth, "maxPages": max_pages, **kwargs}

        if include_paths:
            data["includePaths"] = include_paths
        if exclude_paths:
            data["excludePaths"] = exclude_paths

        return self._request("POST", "/v1/map", data=data)

    # =========================================================================
    # Job Management Methods
    # =========================================================================

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a specific job"""
        return self._request("GET", f"/v1/jobs/{job_id}")

    def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        scrape_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List your recent jobs"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if scrape_type:
            params["scrapeType"] = scrape_type

        return self._request("GET", "/v1/jobs", params=params)

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running or pending job"""
        return self._request("POST", f"/v1/jobs/{job_id}/cancel")

    def delete_job(self, job_id: str) -> Dict[str, Any]:
        """Delete a completed job"""
        return self._request("DELETE", f"/v1/jobs/{job_id}")

    # =========================================================================
    # Credit Management Methods
    # =========================================================================

    def get_credit_balance(self) -> Dict[str, Any]:
        """Get your credit balance and usage"""
        return self._request("GET", "/v1/users/credits")

    # =========================================================================
    # User Management Methods
    # =========================================================================

    def get_user_profile(self) -> Dict[str, Any]:
        """Get your user profile"""
        return self._request("GET", "/v1/users/profile")

    def update_user_profile(self, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Update your user profile"""
        data = {}
        if full_name:
            data["fullName"] = full_name
        return self._request("PUT", "/v1/users/profile", data=data)

    # =========================================================================
    # API Key Management Methods
    # =========================================================================

    def list_api_keys(self) -> Dict[str, Any]:
        """List your API keys"""
        return self._request("GET", "/v1/api-keys")

    def create_api_key(
        self, name: str, expires_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new API key"""
        data = {"name": name}
        if expires_at:
            data["expiresAt"] = expires_at
        return self._request("POST", "/v1/api-keys", data=data)

    def delete_api_key(self, key_id: str) -> Dict[str, Any]:
        """Delete an API key"""
        return self._request("DELETE", f"/v1/api-keys/{key_id}")
