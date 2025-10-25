"""Exception hierarchy for ArkForge SDK.

This module defines all exceptions that can be raised by the SDK,
organized in a clear hierarchy for easy catching and handling.
"""

from typing import Any, Optional


class ArkForgeError(Exception):
    """Base exception for all SDK errors.

    All SDK exceptions inherit from this base class, making it easy to catch
    all SDK-related errors with a single except clause.

    Attributes:
        message: Human-readable error message
        code: Error code (e.g., E_INVALID_PARAMETERS)
        status_code: HTTP status code if applicable
        details: Additional error details (dict, list, etc.)
        request_id: Request ID for support/debugging
        retryable: Whether this error can be retried
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Any] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        self.request_id = request_id
        self.retryable = False  # Default: not retryable
        super().__init__(message)

    def __str__(self) -> str:
        """String representation with code and request ID."""
        parts = [self.message]
        if self.code:
            parts.append(f"(code={self.code})")
        if self.request_id:
            parts.append(f"[request_id={self.request_id}]")
        return " ".join(parts)

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"status_code={self.status_code}, "
            f"request_id={self.request_id!r})"
        )


# Validation Errors (400) - NOT retryable
class ValidationError(ArkForgeError):
    """Invalid request parameters.

    Raised when the request contains invalid or missing parameters.
    This error is not retryable - the request must be fixed.
    """

    pass


class InvalidParametersError(ValidationError):
    """Invalid parameters provided in request."""

    pass


class InvalidRiskProfileError(ValidationError):
    """Invalid risk profile specified."""

    pass


class InvalidAssetsError(ValidationError):
    """Invalid asset symbols provided."""

    pass


# Authentication Errors (401) - NOT retryable
class AuthenticationError(ArkForgeError):
    """Authentication failed.

    Raised when API key is invalid, expired, or missing.
    This error is not retryable - check your API key.
    """

    pass


class InvalidApiKeyError(AuthenticationError):
    """Invalid API key format or value."""

    pass


class ExpiredApiKeyError(AuthenticationError):
    """API key has expired."""

    pass


# Rate Limit Errors (429) - RETRYABLE
class RateLimitError(ArkForgeError):
    """Rate limit exceeded.

    Raised when you've made too many requests in a time window.
    This error is retryable - wait for retry_after seconds.

    Attributes:
        retry_after: Seconds to wait before retrying
    """

    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after  # Seconds until retry allowed
        self.retryable = True


# Timeout Errors (504) - RETRYABLE
class TimeoutError(ArkForgeError):
    """Request timeout.

    Raised when a request takes too long to complete.
    This error is retryable.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retryable = True


# Service Errors (5xx) - RETRYABLE
class ServiceError(ArkForgeError):
    """Server-side error.

    Raised when the ArkForge service encounters an internal error.
    This error is retryable.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retryable = True


class ForecastFailedError(ServiceError):
    """TimeGPT forecast generation failed."""

    pass


class SentimentFailedError(ServiceError):
    """Sentiment analysis failed."""

    pass


class SynthesisFailedError(ServiceError):
    """LLM synthesis failed."""

    pass


# Network Errors - RETRYABLE
class NetworkError(ArkForgeError):
    """Network communication error.

    Raised when network-level errors occur (connection failed, DNS errors, etc.).
    This error is retryable.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retryable = True


class ConnectionError(NetworkError):
    """Connection to server failed."""

    pass


class DNSError(NetworkError):
    """DNS resolution failed."""

    pass
