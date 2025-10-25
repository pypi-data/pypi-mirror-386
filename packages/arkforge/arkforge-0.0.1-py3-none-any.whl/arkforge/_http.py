"""HTTP client implementation for ArkForge API.

This module provides the HTTP transport layer with retry logic,
rate limiting, and proper error handling.
"""

from typing import Any, Dict, Optional

import httpx

from ._rate_limiter import RateLimiter
from ._retry import RetryPolicy
from .config import ArkForgeConfig
from .errors import (
    ArkForgeError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ServiceError,
    ValidationError,
)
from .errors import (
    TimeoutError as ArkForgeTimeoutError,
)


class HTTPClient:
    """HTTP client with retry and rate limiting support.

    This client handles all HTTP communication with the ArkForge API,
    including automatic retries, rate limiting, and error handling.

    Supports both synchronous and asynchronous operations.

    Attributes:
        config: ArkForge configuration
    """

    def __init__(self, config: ArkForgeConfig):
        """Initialize HTTP client.

        Args:
            config: ArkForge configuration
        """
        self.config = config
        self._retry_policy = RetryPolicy(
            max_attempts=config.retry_attempts, base_delay=config.retry_delay
        )
        self._rate_limiter = RateLimiter()

        # Create synchronous client
        self._client = httpx.Client(
            base_url=config.base_url, timeout=config.timeout, headers=self._build_headers()
        )

        # Async client (lazy initialized)
        self._async_client: Optional[httpx.AsyncClient] = None

    def _build_headers(self) -> Dict[str, str]:
        """Build standard request headers.

        Returns:
            Dict of HTTP headers
        """
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "X-Client-Version": self.config.version,
        }
        if self.config.user_agent:
            headers["User-Agent"] = self.config.user_agent
        return headers

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make synchronous HTTP request with retry and rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., /api/v1/portfolio/optimize)
            json: JSON request body
            params: Query parameters

        Returns:
            Response data as dict

        Raises:
            ValidationError: Invalid request parameters
            AuthenticationError: Authentication failed
            RateLimitError: Rate limit exceeded
            ServiceError: Server error
            NetworkError: Network error
        """

        @self._retry_policy.with_retry
        def _make_request() -> Dict[str, Any]:
            # Acquire rate limit token
            self._rate_limiter.acquire()

            try:
                response = self._client.request(method=method, url=path, json=json, params=params)
            except httpx.TimeoutException as e:
                raise ArkForgeTimeoutError(f"Request timeout after {self.config.timeout}s") from e
            except httpx.NetworkError as e:
                raise NetworkError(f"Network error: {str(e)}") from e

            # Update rate limiter from response headers
            self._rate_limiter.update_from_headers(dict(response.headers))

            # Handle errors
            self._handle_response(response)

            # Return JSON response
            json_response: Dict[str, Any] = response.json()
            return json_response

        return _make_request()

    async def request_async(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make asynchronous HTTP request with retry and rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            json: JSON request body
            params: Query parameters

        Returns:
            Response data as dict

        Raises:
            ValidationError: Invalid request parameters
            AuthenticationError: Authentication failed
            RateLimitError: Rate limit exceeded
            ServiceError: Server error
            NetworkError: Network error
        """
        # Initialize async client if needed
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._build_headers(),
            )

        @self._retry_policy.with_retry_async
        async def _make_request() -> Dict[str, Any]:
            # Acquire rate limit token
            await self._rate_limiter.acquire_async()

            try:
                response = await self._async_client.request(  # type: ignore
                    method=method, url=path, json=json, params=params
                )
            except httpx.TimeoutException as e:
                raise ArkForgeTimeoutError(f"Request timeout after {self.config.timeout}s") from e
            except httpx.NetworkError as e:
                raise NetworkError(f"Network error: {str(e)}") from e

            # Update rate limiter from response headers
            self._rate_limiter.update_from_headers(dict(response.headers))

            # Handle errors
            self._handle_response(response)

            # Return JSON response
            json_response: Dict[str, Any] = response.json()
            return json_response

        return await _make_request()

    def _handle_response(self, response: httpx.Response) -> None:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response

        Raises:
            ArkForgeError: Appropriate exception based on status code
        """
        # Success - no error
        if response.is_success:
            return

        # Parse error response
        try:
            error_data = response.json()
            error_info = error_data.get("error", {})
            code = error_info.get("code")
            message = error_info.get("message", "Unknown error")
            details = error_info.get("details")
            request_id = error_data.get("metadata", {}).get("requestId")
        except Exception:
            # Failed to parse error response
            message = response.text or f"HTTP {response.status_code}"
            code = None
            details = None
            request_id = None

        # Map status codes to exceptions
        if response.status_code == 400:
            raise ValidationError(
                message,
                code=code,
                status_code=response.status_code,
                details=details,
                request_id=request_id,
            )
        elif response.status_code == 401:
            raise AuthenticationError(
                message,
                code=code,
                status_code=response.status_code,
                details=details,
                request_id=request_id,
            )
        elif response.status_code == 429:
            # Extract retry-after from header
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                message,
                retry_after=retry_after,
                code=code,
                status_code=response.status_code,
                details=details,
                request_id=request_id,
            )
        elif response.status_code >= 500:
            raise ServiceError(
                message,
                code=code,
                status_code=response.status_code,
                details=details,
                request_id=request_id,
            )
        else:
            # Generic error for other status codes
            raise ArkForgeError(
                message,
                code=code,
                status_code=response.status_code,
                details=details,
                request_id=request_id,
            )

    def close(self) -> None:
        """Close HTTP clients.

        This should be called when done with the client to clean up resources.
        """
        self._client.close()
        if self._async_client:
            # Note: Async close needs to be awaited
            # User should use async context manager instead
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._async_client.aclose())
                else:
                    loop.run_until_complete(self._async_client.aclose())
            except Exception:
                pass  # Best effort cleanup

    def __enter__(self) -> "HTTPClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
