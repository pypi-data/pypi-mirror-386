import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from arcade_core.errors import (
    UpstreamError,
    UpstreamRateLimitError,
)

logger = logging.getLogger(__name__)

RATE_HEADERS = ("retry-after", "x-ratelimit-reset", "x-ratelimit-reset-ms")


class BaseHTTPErrorMapper:
    """Base class for HTTP error mapping functionality."""

    def _parse_retry_ms(self, headers: dict[str, str]) -> int:
        """
        Parses a rate limit header and returns the number
        of milliseconds until the rate limit resets.

        Args:
            headers: A dictionary of HTTP headers.

        Returns:
            The number of milliseconds until the rate limit resets.
            Defaults to 1000ms if a rate limit header is not found or cannot be parsed.
        """
        val = next((headers.get(h) for h in RATE_HEADERS if headers.get(h)), None)
        # No rate limit header found
        if val is None:
            return 1_000
        # Rate limit header is a number of seconds
        if val.isdigit():
            key = next((h for h in RATE_HEADERS if headers.get(h) == val), "")
            if key.endswith("ms"):
                return int(val)
            return int(val) * 1_000
        # Rate limit header is an absolute date
        try:
            dt = datetime.strptime(val, "%a, %d %b %Y %H:%M:%S %Z")
            return int((dt - datetime.now(timezone.utc)).total_seconds() * 1_000)
        except Exception:
            logger.warning(f"Failed to parse rate limit header: {val}. Defaulting to 1000ms.")
            return 1_000

    def _sanitize_uri(self, uri: str) -> str:
        """Strip query params and fragments from URI for privacy."""

        parsed = urlparse(uri)
        return f"{parsed.scheme}://{parsed.netloc.strip('/')}/{parsed.path.strip('/')}"

    def _build_extra_metadata(
        self, request_url: str | None = None, request_method: str | None = None
    ) -> dict[str, str]:
        """Build extra metadata for error reporting."""
        extra = {
            "service": HTTPErrorAdapter.slug,
        }

        if request_url:
            extra["endpoint"] = self._sanitize_uri(request_url)

        if request_method:
            extra["http_method"] = request_method.upper()

        return extra

    def _map_status_to_error(
        self,
        status: int,
        headers: dict[str, str],
        msg: str,
        request_url: str | None = None,
        request_method: str | None = None,
    ) -> UpstreamError:
        """Map HTTP status code to appropriate Arcade error."""
        extra = self._build_extra_metadata(request_url, request_method)

        # Special case for rate limiting
        if status == 429:
            return UpstreamRateLimitError(
                retry_after_ms=self._parse_retry_ms(headers),
                message=msg,
                extra=extra,
            )

        if status == 403 and self._is_rate_limit_403(headers, msg):
            return UpstreamRateLimitError(
                retry_after_ms=self._parse_retry_ms(headers),
                message=msg,
                extra=extra,
            )

        return UpstreamError(message=msg, status_code=status, extra=extra)

    def _is_rate_limit_403(self, headers: dict[str, str], msg: str) -> bool:
        """
        Determine if a 403 error is actually a rate limiting error.

        Simply checks if any rate limiting headers are present.

        Args:
            headers: HTTP response headers
            msg: Error message (unused, kept for compatibility)

        Returns:
            True if this 403 should be treated as rate limiting
        """
        # Check if any rate limiting headers are present
        return any(header.lower() in [h.lower() for h in headers] for header in RATE_HEADERS)


class _HTTPXExceptionHandler:
    """Handler for httpx-specific exceptions."""

    def handle_exception(self, exc: Any, mapper: BaseHTTPErrorMapper) -> UpstreamError | None:
        """Handle httpx HTTPStatusError exceptions.

        Args:
            exc: An httpx.HTTPStatusError exception
            mapper: The BaseHTTPErrorMapper instance to use for mapping

        Returns:
            An Arcade error instance or None if not an httpx exception
        """
        # Lazy import httpx types locally to avoid import errors for toolkits that don't use httpx
        try:
            import httpx
        except ImportError:
            return None

        if not isinstance(exc, httpx.HTTPStatusError):
            return None

        response = exc.response
        request_url = None
        request_method = None
        if hasattr(exc, "request") and exc.request:
            request_url = str(exc.request.url)
            request_method = exc.request.method

        return mapper._map_status_to_error(
            response.status_code,
            dict(response.headers),
            str(exc),
            request_url=request_url,
            request_method=request_method,
        )


class _RequestsExceptionHandler:
    """Handler for requests-specific exceptions."""

    def handle_exception(self, exc: Any, mapper: BaseHTTPErrorMapper) -> UpstreamError | None:
        """Handle requests library exceptions.

        Args:
            exc: A requests.exceptions.HTTPError exception
            mapper: The BaseHTTPErrorMapper instance to use for mapping

        Returns:
            An Arcade error instance or None if not a requests exception
        """
        # Lazy import requests types locally to avoid import errors for toolkits that don't use requests
        try:
            from requests.exceptions import HTTPError  # type: ignore[import-untyped]
        except ImportError:
            return None

        if not isinstance(exc, HTTPError):
            return None

        response = getattr(exc, "response", None)
        if response is None:
            return None

        # Extract request information
        request_url = None
        request_method = None
        if hasattr(response, "request") and response.request:
            request_url = response.request.url
            request_method = response.request.method
        elif hasattr(response, "url"):
            request_url = response.url

        return mapper._map_status_to_error(
            response.status_code,
            dict(response.headers),
            str(exc),
            request_url=request_url,
            request_method=request_method,
        )


class HTTPErrorAdapter(BaseHTTPErrorMapper):
    """Main HTTP error adapter that supports multiple HTTP libraries."""

    slug = "_http"

    def __init__(self) -> None:
        self._httpx_handler = _HTTPXExceptionHandler()
        self._requests_handler = _RequestsExceptionHandler()

    def from_exception(self, exc: Exception) -> UpstreamError | None:
        """Convert HTTP library exceptions into Arcade errors."""

        httpx_result = self._httpx_handler.handle_exception(exc, self)
        if httpx_result is not None:
            return httpx_result

        requests_result = self._requests_handler.handle_exception(exc, self)
        if requests_result is not None:
            return requests_result

        logger.info(
            f"Exception type '{type(exc).__name__}' was not handled by the '{self.slug}' adapter. "
            f"Either the exception is not from a supported HTTP library (httpx, requests) or "
            f"the required library is not installed in the toolkit's environment."
        )
        return None
