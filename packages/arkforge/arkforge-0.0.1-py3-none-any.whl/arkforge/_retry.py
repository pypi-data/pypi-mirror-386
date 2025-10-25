"""Retry policy implementation with exponential backoff.

This module implements retry logic for handling transient failures
when communicating with the ArkForge API.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")


class RetryPolicy:
    """Exponential backoff retry policy.

    This policy automatically retries failed requests with exponential
    backoff for retryable errors (rate limits, server errors, timeouts).

    Retry on:
        - HTTP 429 (Rate Limit)
        - HTTP 5xx (Server Errors)
        - Network errors
        - Timeouts

    Do NOT retry on:
        - HTTP 400 (Bad Request)
        - HTTP 401 (Unauthorized)
        - HTTP 404 (Not Found)
        - Validation errors

    Exponential backoff formula:
        delay = base_delay * (2 ^ attempt)

    Example:
        Attempt 1: Immediate
        Attempt 2: Wait 1s  (1 * 2^0)
        Attempt 3: Wait 2s  (1 * 2^1)
        Attempt 4: Wait 4s  (1 * 2^2)

    Attributes:
        max_attempts: Maximum retry attempts (default: 3)
        base_delay: Base delay in seconds (default: 1.0)
    """

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        """Initialize retry policy.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for synchronous retry logic.

        Args:
            func: Function to wrap with retry logic

        Returns:
            Wrapped function with retry behavior

        Example:
            >>> policy = RetryPolicy(max_attempts=3)
            >>> @policy.with_retry
            ... def make_request():
            ...     # Request logic here
            ...     pass
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(self.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if error is retryable
                    if not self._is_retryable(e):
                        raise

                    # Last attempt - raise the error
                    if attempt == self.max_attempts - 1:
                        raise

                    # Calculate delay for next retry
                    delay = self._calculate_delay(attempt, e)

                    # Sleep before retry
                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception  # type: ignore

        return wrapper

    def with_retry_async(
        self, func: Callable[..., Coroutine[Any, Any, T]]
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        """Decorator for asynchronous retry logic.

        Args:
            func: Async function to wrap with retry logic

        Returns:
            Wrapped async function with retry behavior

        Example:
            >>> policy = RetryPolicy(max_attempts=3)
            >>> @policy.with_retry_async
            ... async def make_request():
            ...     # Async request logic here
            ...     pass
        """

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(self.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if error is retryable
                    if not self._is_retryable(e):
                        raise

                    # Last attempt - raise the error
                    if attempt == self.max_attempts - 1:
                        raise

                    # Calculate delay for next retry
                    delay = self._calculate_delay(attempt, e)

                    # Await sleep before retry
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception  # type: ignore

        return wrapper

    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error can be retried, False otherwise
        """
        from .errors import ArkForgeError, AuthenticationError, ValidationError

        # Don't retry validation or authentication errors
        if isinstance(error, (ValidationError, AuthenticationError)):
            return False

        # Retry SDK errors marked as retryable
        if isinstance(error, ArkForgeError):
            return error.retryable

        # Retry on httpx network/timeout errors
        try:
            import httpx

            if isinstance(error, (httpx.TimeoutException, httpx.NetworkError)):
                return True
        except ImportError:
            pass

        # Don't retry by default
        return False

    def _calculate_delay(self, attempt: int, error: Exception) -> float:
        """Calculate delay for next retry with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)
            error: Exception that triggered retry

        Returns:
            Delay in seconds before next retry
        """
        from .errors import RateLimitError

        # Respect Retry-After header for rate limit errors
        if isinstance(error, RateLimitError) and error.retry_after:
            return float(error.retry_after)

        # Exponential backoff: delay = base_delay * (2 ^ attempt)
        return float(self.base_delay * (2**attempt))
