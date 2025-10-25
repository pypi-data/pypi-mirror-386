"""Rate limiter implementation using token bucket algorithm.

This module implements client-side rate limiting to prevent exceeding API quotas.
The rate limiter tracks server-provided rate limit headers and manages tokens
accordingly.
"""

import asyncio
import time
from threading import Lock
from typing import Dict, Optional


class RateLimiter:
    """Token bucket rate limiter with server-guided limits.

    This rate limiter uses the token bucket algorithm and updates its state
    based on rate limit headers from the API server.

    Rate limit headers:
        X-RateLimit-Limit: Maximum requests per window
        X-RateLimit-Remaining: Remaining requests in window
        X-RateLimit-Reset: Unix timestamp when limit resets

    Thread-safe for concurrent usage.

    Example:
        >>> limiter = RateLimiter()
        >>> limiter.acquire()  # Block if no tokens
        >>> # Make request
        >>> limiter.update_from_headers(response.headers)
    """

    def __init__(self) -> None:
        """Initialize rate limiter."""
        self._lock = Lock()
        self._tokens: Optional[int] = None  # Available tokens
        self._limit: Optional[int] = None  # Max tokens per window
        self._reset_at: Optional[float] = None  # Unix timestamp for reset

    def update_from_headers(self, headers: Dict[str, str]) -> None:
        """Update rate limit state from response headers.

        This method should be called after each API response to update
        the rate limiter's state based on server-provided information.

        Args:
            headers: Response headers dict
        """
        with self._lock:
            # Update limit if provided
            if "X-RateLimit-Limit" in headers:
                self._limit = int(headers["X-RateLimit-Limit"])

            # Update remaining tokens if provided
            if "X-RateLimit-Remaining" in headers:
                self._tokens = int(headers["X-RateLimit-Remaining"])

            # Update reset time if provided
            if "X-RateLimit-Reset" in headers:
                self._reset_at = float(headers["X-RateLimit-Reset"])

    def acquire(self) -> None:
        """Acquire a token (synchronous).

        This method blocks if no tokens are available, waiting until
        the rate limit resets.

        Example:
            >>> limiter.acquire()  # Blocks if rate limited
            >>> # Proceed with request
        """
        while True:
            with self._lock:
                # Refill tokens if past reset time
                if self._reset_at and time.time() >= self._reset_at:
                    self._tokens = self._limit

                # If we don't know the limit yet, allow the request
                # (server will tell us on first response)
                if self._tokens is None:
                    return

                # If tokens available, consume one and proceed
                if self._tokens > 0:
                    self._tokens -= 1
                    return

                # Calculate wait time until reset
                wait_time = max(0, self._reset_at - time.time()) if self._reset_at else 1

            # Wait outside the lock to allow other threads
            time.sleep(wait_time)

    async def acquire_async(self) -> None:
        """Acquire a token (asynchronous).

        This method awaits if no tokens are available, waiting until
        the rate limit resets.

        Example:
            >>> await limiter.acquire_async()
            >>> # Proceed with async request
        """
        while True:
            with self._lock:
                # Refill tokens if past reset time
                if self._reset_at and time.time() >= self._reset_at:
                    self._tokens = self._limit

                # If we don't know the limit yet, allow the request
                if self._tokens is None:
                    return

                # If tokens available, consume one and proceed
                if self._tokens > 0:
                    self._tokens -= 1
                    return

                # Calculate wait time until reset
                wait_time = max(0, self._reset_at - time.time()) if self._reset_at else 1

            # Await outside the lock
            await asyncio.sleep(wait_time)

    @property
    def tokens_remaining(self) -> Optional[int]:
        """Get remaining tokens (for monitoring).

        Returns:
            Number of remaining tokens, or None if unknown
        """
        with self._lock:
            return self._tokens

    @property
    def limit(self) -> Optional[int]:
        """Get rate limit (for monitoring).

        Returns:
            Rate limit per window, or None if unknown
        """
        with self._lock:
            return self._limit

    @property
    def reset_at(self) -> Optional[float]:
        """Get reset timestamp (for monitoring).

        Returns:
            Unix timestamp when limit resets, or None if unknown
        """
        with self._lock:
            return self._reset_at
