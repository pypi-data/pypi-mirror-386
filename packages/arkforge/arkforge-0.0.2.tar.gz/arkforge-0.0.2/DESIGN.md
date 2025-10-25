# ArkForge Python SDK - Technical Design Document

**Version**: 1.0.0
**Date**: October 23, 2025
**Status**: Design Approved

---

## Executive Summary

This document outlines the technical design for the ArkForge Python SDK, a production-ready client library for the ArkForge DeFi portfolio management service. The SDK follows modern Python best practices and provides a type-safe, robust, and developer-friendly interface.

**Key Design Goals**:
- World-class developer experience (DX) matching Stripe, OpenAI, Anthropic SDKs
- Type safety with comprehensive type hints and Pydantic validation
- Resilient architecture with retry logic, rate limiting, and error handling
- Both synchronous and asynchronous API support
- >85% test coverage with comprehensive test suite
- Excellent documentation and examples

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Package Structure](#package-structure)
3. [Core Components](#core-components)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Client API Design](#client-api-design)
7. [HTTP Transport Layer](#http-transport-layer)
8. [Configuration Management](#configuration-management)
9. [Testing Strategy](#testing-strategy)
10. [Development Workflow](#development-workflow)
11. [Performance Considerations](#performance-considerations)
12. [Security Design](#security-design)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│              User Application                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│          ArkForge Python SDK                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────┐         │
│  │       Public API Layer                 │         │
│  │  • ArkForgeClient                      │         │
│  │  • KeyManagementClient                 │         │
│  └────────────────┬───────────────────────┘         │
│                   │                                  │
│  ┌────────────────▼───────────────────────┐         │
│  │       Transport Layer                  │         │
│  │  • HTTPClient (sync/async)             │         │
│  │  • RetryPolicy (exponential backoff)   │         │
│  │  • RateLimiter (token bucket)          │         │
│  └────────────────┬───────────────────────┘         │
│                   │                                  │
│  ┌────────────────▼───────────────────────┐         │
│  │       Model Layer                      │         │
│  │  • Request Models (Pydantic)           │         │
│  │  • Response Models (Pydantic)          │         │
│  │  • Validation & Serialization          │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  ┌────────────────────────────────────────┐         │
│  │       Configuration & Errors           │         │
│  │  • ArkForgeConfig                      │         │
│  │  • Exception Hierarchy                 │         │
│  └────────────────────────────────────────┘         │
│                                                      │
└─────────────────────┼──────────────────────────────┘
                      │
                      ↓ HTTPS
┌─────────────────────────────────────────────────────┐
│          ArkForge REST API Service                   │
│        http://localhost:3001/api/v1                  │
└─────────────────────────────────────────────────────┘
```

### 1.2 Layer Responsibilities

**Public API Layer**:
- User-facing client classes
- Method signatures and documentation
- High-level business logic
- Request/response transformation

**Transport Layer**:
- HTTP communication (httpx)
- Retry logic with exponential backoff
- Rate limiting and quota management
- Request/response lifecycle

**Model Layer**:
- Data validation (Pydantic v2)
- Type safety and serialization
- Business rule validation
- Immutable data structures

**Configuration & Errors**:
- SDK configuration management
- Exception hierarchy
- Error code mapping
- Logging integration

---

## 2. Package Structure

### 2.1 Directory Layout

```
arkforge-sdk-py/
├── arkforge/                       # Main package
│   ├── __init__.py                # Public API exports
│   ├── version.py                 # Version constant
│   ├── client.py                  # ArkForgeClient (portfolio operations)
│   ├── key_management.py          # KeyManagementClient (key lifecycle)
│   ├── config.py                  # ArkForgeConfig class
│   ├── errors.py                  # Exception hierarchy
│   │
│   ├── models/                    # Data models package
│   │   ├── __init__.py           # Model exports
│   │   ├── requests.py           # Request models (Pydantic)
│   │   ├── responses.py          # Response models (Pydantic)
│   │   └── common.py             # Shared models, enums
│   │
│   ├── _base_client.py           # Base client implementation (private)
│   ├── _http.py                  # HTTP client (sync/async) (private)
│   ├── _retry.py                 # Retry policy logic (private)
│   └── _rate_limiter.py          # Rate limiter implementation (private)
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration & fixtures
│   ├── unit/                     # Unit tests (isolated)
│   │   ├── test_client.py
│   │   ├── test_key_management.py
│   │   ├── test_config.py
│   │   ├── test_errors.py
│   │   ├── test_retry.py
│   │   ├── test_rate_limiter.py
│   │   ├── test_http.py
│   │   └── test_models.py
│   ├── integration/              # Integration tests (real API)
│   │   ├── test_portfolio_api.py
│   │   ├── test_key_api.py
│   │   └── test_error_scenarios.py
│   └── fixtures/                 # Test data fixtures
│       ├── requests.json
│       └── responses.json
│
├── examples/                      # Usage examples
│   ├── basic_usage.py
│   ├── portfolio_optimization.py
│   ├── key_management.py
│   ├── error_handling.py
│   └── async_usage.py
│
├── docs/                          # Documentation
│   ├── index.md
│   ├── quickstart.md
│   ├── api_reference.md
│   └── migration_guide.md
│
├── .github/                       # GitHub workflows
│   └── workflows/
│       ├── ci.yml
│       └── publish.yml
│
├── pyproject.toml                 # Modern Python project config
├── README.md                      # Main documentation
├── LICENSE                        # MIT License
├── CHANGELOG.md                   # Version history
└── CONTRIBUTING.md                # Contribution guidelines
```

### 2.2 Public API Surface

**Exports from `arkforge/__init__.py`**:

```python
# Public clients
from .client import ArkForgeClient
from .key_management import KeyManagementClient

# Configuration
from .config import ArkForgeConfig

# Request models
from .models import (
    OptimizePortfolioRequest,
    CreateKeyRequest,
    # ... other request models
)

# Response models
from .models import (
    PortfolioRecommendation,
    RiskProfile,
    CreateKeyResponse,
    # ... other response models
)

# Exceptions
from .errors import (
    ArkForgeError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    # ... other exceptions
)

# Version
from .version import __version__

__all__ = [
    # Clients
    "ArkForgeClient",
    "KeyManagementClient",
    # Config
    "ArkForgeConfig",
    # Models (selected commonly used)
    "OptimizePortfolioRequest",
    "PortfolioRecommendation",
    # Errors (commonly caught)
    "ArkForgeError",
    "ValidationError",
    "RateLimitError",
    # Version
    "__version__",
]
```

**Private Modules** (prefixed with `_`):
- `_base_client.py`: Shared client logic (not exported)
- `_http.py`: HTTP transport (not exported)
- `_retry.py`: Retry policy (not exported)
- `_rate_limiter.py`: Rate limiter (not exported)

---

## 3. Core Components

### 3.1 HTTP Client (`_http.py`)

**Purpose**: Handle all HTTP communication with the ArkForge API.

**Design**:

```python
from typing import Dict, Any, Optional
import httpx
from .config import ArkForgeConfig
from .errors import NetworkError, TimeoutError
from ._retry import RetryPolicy
from ._rate_limiter import RateLimiter

class HTTPClient:
    """HTTP client with retry and rate limiting support.

    Supports both synchronous and asynchronous operations.
    """

    def __init__(self, config: ArkForgeConfig):
        self.config = config
        self._retry_policy = RetryPolicy(
            max_attempts=config.retry_attempts,
            base_delay=config.retry_delay
        )
        self._rate_limiter = RateLimiter()

        # Sync client
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=self._build_headers()
        )

        # Async client (lazy initialized)
        self._async_client: Optional[httpx.AsyncClient] = None

    def _build_headers(self) -> Dict[str, str]:
        """Build standard request headers."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": self.config.user_agent,
            "X-Client-Version": self.config.version,
        }

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make synchronous HTTP request with retry and rate limiting."""

        @self._retry_policy.with_retry
        def _make_request():
            # Acquire rate limit token
            self._rate_limiter.acquire()

            response = self._client.request(
                method=method,
                url=path,
                json=json,
                params=params
            )

            # Update rate limiter from response headers
            self._rate_limiter.update_from_headers(response.headers)

            # Handle errors
            self._handle_response(response)

            return response.json()

        return _make_request()

    async def request_async(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make asynchronous HTTP request with retry and rate limiting."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._build_headers()
            )

        @self._retry_policy.with_retry_async
        async def _make_request():
            await self._rate_limiter.acquire_async()

            response = await self._async_client.request(
                method=method,
                url=path,
                json=json,
                params=params
            )

            self._rate_limiter.update_from_headers(response.headers)
            self._handle_response(response)

            return response.json()

        return await _make_request()

    def _handle_response(self, response: httpx.Response) -> None:
        """Handle HTTP response and raise appropriate exceptions."""
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
            message = response.text
            code = None
            details = None
            request_id = None

        # Map to SDK exceptions (see errors.py design)
        from .errors import (
            ValidationError,
            AuthenticationError,
            RateLimitError,
            ServiceError,
        )

        if response.status_code == 400:
            raise ValidationError(message, code, response.status_code, details, request_id)
        elif response.status_code == 401:
            raise AuthenticationError(message, code, response.status_code, details, request_id)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(message, retry_after, code, response.status_code, details, request_id)
        elif response.status_code >= 500:
            raise ServiceError(message, code, response.status_code, details, request_id)
        else:
            raise ArkForgeError(message, code, response.status_code, details, request_id)

    def close(self):
        """Close HTTP clients."""
        self._client.close()
        if self._async_client:
            # Note: async close requires await
            import asyncio
            asyncio.create_task(self._async_client.aclose())
```

**Key Features**:
- ✅ Sync and async support via httpx
- ✅ Automatic retry with exponential backoff
- ✅ Rate limiting integration
- ✅ Proper error mapping
- ✅ Request ID tracking
- ✅ Context manager support

### 3.2 Retry Policy (`_retry.py`)

**Purpose**: Implement exponential backoff retry logic.

**Design**:

```python
import time
import asyncio
from typing import Callable, TypeVar, Optional
from functools import wraps

T = TypeVar('T')

class RetryPolicy:
    """Exponential backoff retry policy.

    Retry on:
    - HTTP 429 (Rate Limit)
    - HTTP 5xx (Server Errors)
    - Network errors
    - Timeouts

    Do NOT retry on:
    - HTTP 400 (Bad Request)
    - HTTP 401 (Unauthorized)
    - HTTP 404 (Not Found)
    """

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay

    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for synchronous retry logic."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(self.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if retryable
                    if not self._is_retryable(e):
                        raise

                    # Last attempt - raise
                    if attempt == self.max_attempts - 1:
                        raise

                    # Calculate delay
                    delay = self._calculate_delay(attempt, e)

                    # Sleep before retry
                    time.sleep(delay)

            raise last_exception

        return wrapper

    def with_retry_async(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for asynchronous retry logic."""
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(self.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not self._is_retryable(e):
                        raise

                    if attempt == self.max_attempts - 1:
                        raise

                    delay = self._calculate_delay(attempt, e)
                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper

    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable."""
        from .errors import (
            ArkForgeError,
            ValidationError,
            AuthenticationError,
        )

        # Don't retry validation or auth errors
        if isinstance(error, (ValidationError, AuthenticationError)):
            return False

        # Retry on SDK errors marked as retryable
        if isinstance(error, ArkForgeError):
            return error.retryable

        # Retry on network errors
        import httpx
        if isinstance(error, (httpx.TimeoutException, httpx.NetworkError)):
            return True

        return False

    def _calculate_delay(self, attempt: int, error: Exception) -> float:
        """Calculate delay for next retry with exponential backoff."""
        from .errors import RateLimitError

        # Respect Retry-After for rate limit errors
        if isinstance(error, RateLimitError) and error.retry_after:
            return error.retry_after

        # Exponential backoff: delay = base_delay * (2 ^ attempt)
        return self.base_delay * (2 ** attempt)
```

**Algorithm**:
- Attempt 1: Immediate
- Attempt 2: Wait 1s (1 * 2^0)
- Attempt 3: Wait 2s (1 * 2^1)
- Attempt 4: Wait 4s (1 * 2^2)

### 3.3 Rate Limiter (`_rate_limiter.py`)

**Purpose**: Client-side rate limiting using token bucket algorithm.

**Design**:

```python
import time
import asyncio
from threading import Lock
from typing import Optional

class RateLimiter:
    """Token bucket rate limiter.

    Tracks rate limit from API response headers:
    - X-RateLimit-Limit: Max requests per window
    - X-RateLimit-Remaining: Remaining requests
    - X-RateLimit-Reset: Unix timestamp when limit resets
    """

    def __init__(self):
        self._lock = Lock()
        self._tokens: Optional[int] = None
        self._limit: Optional[int] = None
        self._reset_at: Optional[float] = None

    def update_from_headers(self, headers: dict) -> None:
        """Update rate limit state from response headers."""
        with self._lock:
            if "X-RateLimit-Limit" in headers:
                self._limit = int(headers["X-RateLimit-Limit"])

            if "X-RateLimit-Remaining" in headers:
                self._tokens = int(headers["X-RateLimit-Remaining"])

            if "X-RateLimit-Reset" in headers:
                self._reset_at = float(headers["X-RateLimit-Reset"])

    def acquire(self) -> None:
        """Acquire a token (synchronous). Blocks if no tokens available."""
        while True:
            with self._lock:
                # Refill if past reset time
                if self._reset_at and time.time() >= self._reset_at:
                    self._tokens = self._limit

                # If we don't know the limit yet, allow request
                if self._tokens is None:
                    return

                # If tokens available, consume one
                if self._tokens > 0:
                    self._tokens -= 1
                    return

                # Calculate wait time
                if self._reset_at:
                    wait_time = max(0, self._reset_at - time.time())
                else:
                    wait_time = 1  # Default wait

            # Wait outside lock
            time.sleep(wait_time)

    async def acquire_async(self) -> None:
        """Acquire a token (asynchronous). Awaits if no tokens available."""
        while True:
            with self._lock:
                if self._reset_at and time.time() >= self._reset_at:
                    self._tokens = self._limit

                if self._tokens is None:
                    return

                if self._tokens > 0:
                    self._tokens -= 1
                    return

                if self._reset_at:
                    wait_time = max(0, self._reset_at - time.time())
                else:
                    wait_time = 1

            await asyncio.sleep(wait_time)
```

**Features**:
- ✅ Thread-safe token bucket
- ✅ Server-guided rate limiting
- ✅ Automatic refill at reset time
- ✅ Sync and async support

---

## 4. Data Models

### 4.1 Technology Choice: Pydantic v2

**Rationale**:
- ✅ Automatic validation with clear error messages
- ✅ JSON serialization/deserialization built-in
- ✅ Type hints for excellent IDE support
- ✅ Immutable models (frozen) for thread safety
- ✅ Field validators for business logic
- ✅ JSON Schema generation
- ✅ Performance (Pydantic v2 is Rust-based)

### 4.2 Request Models (`models/requests.py`)

```python
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator
from .common import RiskProfileType, OptimizationGoal

class OptimizationConfig(BaseModel):
    """Portfolio optimization configuration."""
    target_sharpe_ratio: Optional[float] = Field(None, ge=0, description="Target Sharpe ratio")
    max_volatility: Optional[float] = Field(None, ge=0, le=1, description="Max volatility (0-1)")
    min_expected_return: Optional[float] = Field(None, ge=0, le=1, description="Min return (0-1)")
    goal: Optional[OptimizationGoal] = Field("sharpe", description="Optimization goal")
    sentiment_weight: Optional[float] = Field(1.0, ge=0, le=1, description="Sentiment weight")
    ignore_sentiment: Optional[bool] = Field(False, description="Ignore sentiment")
    optimistic_bias: Optional[bool] = Field(False, description="Optimistic bias")

    model_config = {"frozen": True}

class Constraints(BaseModel):
    """Portfolio constraints."""
    max_position_size: Optional[float] = Field(None, ge=0, le=100, description="Max % per asset")
    min_diversification: Optional[int] = Field(None, ge=1, description="Min number of assets")
    excluded_assets: Optional[List[str]] = Field(None, description="Assets to exclude")

    model_config = {"frozen": True}

class OptimizePortfolioRequest(BaseModel):
    """Request to optimize portfolio allocation."""

    # Required
    assets: List[str] = Field(..., min_length=1, description="Asset symbols")
    risk_profile: RiskProfileType = Field(..., description="Risk profile")

    # Optional
    current_portfolio: Optional[Dict[str, float]] = Field(None, description="Current allocation")
    budget: Optional[float] = Field(None, gt=0, description="Investment budget")
    horizon_days: Optional[int] = Field(7, ge=1, le=365, description="Forecast horizon")
    sentiment_timeframe_hours: Optional[int] = Field(168, ge=1, description="Sentiment timeframe")

    # Nested configs
    constraints: Optional[Constraints] = None
    optimization: Optional[OptimizationConfig] = None

    @field_validator("assets")
    @classmethod
    def validate_assets(cls, v: List[str]) -> List[str]:
        """Validate asset symbols."""
        if not v:
            raise ValueError("At least one asset required")

        # Uppercase symbols
        return [asset.upper() for asset in v]

    @field_validator("current_portfolio")
    @classmethod
    def validate_portfolio(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate portfolio percentages sum to 100."""
        if v is None:
            return v

        total = sum(v.values())
        if not (99.9 <= total <= 100.1):  # Allow small floating point errors
            raise ValueError(f"Portfolio percentages must sum to 100, got {total}")

        return v

    model_config = {"frozen": True}

class CreateKeyRequest(BaseModel):
    """Request to create API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Key name")
    expires_in_days: Optional[int] = Field(365, ge=1, le=365, description="Expiry days")
    scopes: Optional[List[str]] = Field(None, description="Key scopes")

    model_config = {"frozen": True}
```

### 4.3 Response Models (`models/responses.py`)

```python
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .common import ActionType

class Action(BaseModel):
    """Portfolio action recommendation."""
    action: ActionType
    symbol: str
    target_percentage: float = Field(..., ge=0, le=100)
    current_percentage: float = Field(..., ge=0, le=100)
    change: float = Field(..., ge=-100, le=100)

    model_config = {"frozen": True}

class SwapInstruction(BaseModel):
    """Token swap instruction."""
    type: str = "swap"
    from_token: str
    from_amount: float
    to_token: str
    to_amount: float
    reason: str

    model_config = {"frozen": True}

class Rationale(BaseModel):
    """Optimization rationale."""
    drivers: List[str]
    risks: List[str]
    market_context: str
    forecast_insights: str
    sentiment_insights: str

    model_config = {"frozen": True}

class Metadata(BaseModel):
    """Response metadata."""
    workflow_id: str
    timestamp: datetime
    processing_time: int = Field(..., description="Processing time in ms")
    llm_provider: str
    llm_model: str
    request_id: str

    model_config = {"frozen": True}

class PortfolioRecommendation(BaseModel):
    """Portfolio optimization recommendation."""

    # Allocation
    allocation: Dict[str, float] = Field(..., description="Recommended allocation %")

    # Metrics
    expected_return: float = Field(..., description="Annualized return (0.15 = 15%)")
    expected_volatility: float = Field(..., description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return")
    confidence: float = Field(..., ge=0, le=1, description="Confidence (0-1)")

    # Actions
    actions: List[Action]
    swaps: Optional[List[SwapInstruction]] = None

    # Rationale
    rationale: Optional[Rationale] = None

    # Metadata
    metadata: Metadata

    model_config = {"frozen": True}

class CreateKeyResponse(BaseModel):
    """API key creation response."""
    api_key: str = Field(..., description="Full API key (shown once!)")
    key_id: int
    prefix: str = Field(..., description="Key prefix (first 16 chars)")
    warning: str = "This API key will only be shown once. Store it securely."

    model_config = {"frozen": True}
```

### 4.4 Common Models (`models/common.py`)

```python
from enum import Enum

class RiskProfileType(str, Enum):
    """Risk profile types."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class ActionType(str, Enum):
    """Portfolio action types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class OptimizationGoal(str, Enum):
    """Optimization goals."""
    SHARPE = "sharpe"
    RETURN = "return"
    RISK = "risk"

class HealthStatusType(str, Enum):
    """Health status types."""
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"
```

---

## 5. Error Handling

### 5.1 Exception Hierarchy

```python
# errors.py
from typing import Optional, Any

class ArkForgeError(Exception):
    """Base exception for all SDK errors.

    Attributes:
        message: Human-readable error message
        code: Error code (e.g., E_INVALID_PARAMETERS)
        status_code: HTTP status code
        details: Additional error details
        request_id: Request ID for support
        retryable: Whether error can be retried
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
        parts = [self.message]
        if self.code:
            parts.append(f"(code={self.code})")
        if self.request_id:
            parts.append(f"[request_id={self.request_id}]")
        return " ".join(parts)

# Validation Errors (400) - NOT retryable
class ValidationError(ArkForgeError):
    """Invalid request parameters."""
    pass

class InvalidParametersError(ValidationError):
    """Invalid parameters provided."""
    pass

class InvalidRiskProfileError(ValidationError):
    """Invalid risk profile specified."""
    pass

class InvalidAssetsError(ValidationError):
    """Invalid asset symbols."""
    pass

# Authentication Errors (401) - NOT retryable
class AuthenticationError(ArkForgeError):
    """Authentication failed."""
    pass

class InvalidApiKeyError(AuthenticationError):
    """Invalid API key."""
    pass

class ExpiredApiKeyError(AuthenticationError):
    """Expired API key."""
    pass

# Rate Limit Errors (429) - RETRYABLE
class RateLimitError(ArkForgeError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after  # Seconds until retry
        self.retryable = True

# Timeout Errors (504) - RETRYABLE
class TimeoutError(ArkForgeError):
    """Request timeout."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.retryable = True

# Service Errors (5xx) - RETRYABLE
class ServiceError(ArkForgeError):
    """Server-side error."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.retryable = True

class ForecastFailedError(ServiceError):
    """Forecast generation failed."""
    pass

class SentimentFailedError(ServiceError):
    """Sentiment analysis failed."""
    pass

class SynthesisFailedError(ServiceError):
    """LLM synthesis failed."""
    pass

# Network Errors - RETRYABLE
class NetworkError(ArkForgeError):
    """Network communication error."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, **kwargs)
        self.retryable = True

class ConnectionError(NetworkError):
    """Connection failed."""
    pass

class DNSError(NetworkError):
    """DNS resolution failed."""
    pass
```

### 5.2 Error Code Mapping

| Error Code            | HTTP | Exception                | Retryable |
| --------------------- | ---- | ------------------------ | --------- |
| E_INVALID_PARAMETERS  | 400  | InvalidParametersError   | No        |
| E_INVALID_VAULT       | 400  | ValidationError          | No        |
| E_INVALID_RISK        | 400  | InvalidRiskProfileError  | No        |
| E_UNAUTHORIZED        | 401  | AuthenticationError      | No        |
| E_INVALID_API_KEY     | 401  | InvalidApiKeyError       | No        |
| E_RATE_LIMIT          | 429  | RateLimitError           | Yes       |
| E_RATE_LIMIT_EXCEEDED | 429  | RateLimitError           | Yes       |
| E_TIMEGPT_TIMEOUT     | 502  | ForecastFailedError      | Yes       |
| E_SENTIMENT_FAILED    | 503  | SentimentFailedError     | Yes       |
| E_WORKFLOW_ERROR      | 500  | ServiceError             | Yes       |
| E_TIMEOUT             | 504  | TimeoutError             | Yes       |
| E_INTERNAL_ERROR      | 500  | ServiceError             | Yes       |

---

## 6. Client API Design

### 6.1 ArkForgeClient

```python
# client.py
from typing import List, Optional
from .config import ArkForgeConfig
from ._base_client import BaseClient
from .models import (
    OptimizePortfolioRequest,
    PortfolioRecommendation,
    RiskProfile,
    HealthStatus,
)

class ArkForgeClient(BaseClient):
    """ArkForge portfolio optimization client.

    Example:
        >>> from arkforge import ArkForgeClient
        >>> client = ArkForgeClient(api_key="sk-arkforge-...")
        >>> result = client.optimize_portfolio(
        ...     assets=["BTC", "ETH", "SOL"],
        ...     risk_profile="moderate"
        ... )
        >>> print(result.allocation)
        {'BTC': 40.0, 'ETH': 35.0, 'SOL': 25.0}
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:3001",
        **kwargs
    ):
        """Initialize ArkForge client.

        Args:
            api_key: ArkForge API key (sk-arkforge-...)
            base_url: API base URL (default: http://localhost:3001)
            **kwargs: Additional config (timeout, retry_attempts, etc.)
        """
        config = ArkForgeConfig(api_key=api_key, base_url=base_url, **kwargs)
        super().__init__(config)

    def optimize_portfolio(
        self,
        request: OptimizePortfolioRequest
    ) -> PortfolioRecommendation:
        """Optimize portfolio allocation.

        Args:
            request: Portfolio optimization request

        Returns:
            Portfolio recommendation with allocation and metrics

        Raises:
            ValidationError: Invalid request parameters
            RateLimitError: Rate limit exceeded
            ServiceError: Server error
        """
        response = self._http.request(
            method="POST",
            path="/api/v1/portfolio/optimize",
            json=request.model_dump(exclude_none=True)
        )
        return PortfolioRecommendation.model_validate(response)

    async def optimize_portfolio_async(
        self,
        request: OptimizePortfolioRequest
    ) -> PortfolioRecommendation:
        """Optimize portfolio allocation (async).

        Args:
            request: Portfolio optimization request

        Returns:
            Portfolio recommendation with allocation and metrics
        """
        response = await self._http.request_async(
            method="POST",
            path="/api/v1/portfolio/optimize",
            json=request.model_dump(exclude_none=True)
        )
        return PortfolioRecommendation.model_validate(response)

    def get_risk_profiles(self) -> List[RiskProfile]:
        """Get available risk profiles.

        Returns:
            List of risk profiles with descriptions
        """
        response = self._http.request(
            method="GET",
            path="/api/v1/portfolio/risk-profiles"
        )
        return [RiskProfile.model_validate(rp) for rp in response]

    def health(self) -> HealthStatus:
        """Check service health.

        Returns:
            Health status with service availability
        """
        response = self._http.request(
            method="GET",
            path="/health"
        )
        return HealthStatus.model_validate(response)
```

### 6.2 KeyManagementClient

```python
# key_management.py
from typing import List, Optional
from .config import ArkForgeConfig
from ._base_client import BaseClient
from .models import (
    CreateKeyRequest,
    CreateKeyResponse,
    ApiKeyInfo,
    ApiKeyDetails,
)

class KeyManagementClient(BaseClient):
    """API key management client.

    Example:
        >>> from arkforge import KeyManagementClient
        >>> client = KeyManagementClient(api_key="sk-arkforge-...")
        >>> new_key = client.create_key(name="Production Key")
        >>> print(new_key.api_key)  # Save this!
        sk-arkforge-abc123...
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:3001",
        **kwargs
    ):
        """Initialize key management client.

        Args:
            api_key: Admin API key with key management scope
            base_url: API base URL
            **kwargs: Additional config
        """
        config = ArkForgeConfig(api_key=api_key, base_url=base_url, **kwargs)
        super().__init__(config)

    def create_key(self, request: CreateKeyRequest) -> CreateKeyResponse:
        """Create new API key.

        Args:
            request: Key creation request

        Returns:
            Created key response (includes full API key - shown once!)
        """
        response = self._http.request(
            method="POST",
            path="/api/v1/keys",
            json=request.model_dump(exclude_none=True)
        )
        return CreateKeyResponse.model_validate(response)

    def list_keys(self) -> List[ApiKeyInfo]:
        """List all API keys.

        Returns:
            List of API key info (without full key)
        """
        response = self._http.request(
            method="GET",
            path="/api/v1/keys"
        )
        return [ApiKeyInfo.model_validate(key) for key in response]

    def get_key_details(self, key_id: int) -> ApiKeyDetails:
        """Get API key details with usage stats.

        Args:
            key_id: API key ID

        Returns:
            Key details with usage statistics
        """
        response = self._http.request(
            method="GET",
            path=f"/api/v1/keys/{key_id}"
        )
        return ApiKeyDetails.model_validate(response)

    def revoke_key(self, key_id: int, reason: Optional[str] = None) -> None:
        """Revoke API key.

        Args:
            key_id: API key ID to revoke
            reason: Optional revocation reason
        """
        self._http.request(
            method="DELETE",
            path=f"/api/v1/keys/{key_id}",
            json={"reason": reason} if reason else None
        )

    def rotate_key(
        self,
        key_id: int,
        name: Optional[str] = None
    ) -> CreateKeyResponse:
        """Rotate API key (creates new, revokes old).

        Args:
            key_id: API key ID to rotate
            name: Optional name for new key

        Returns:
            New API key (old key is automatically revoked)
        """
        response = self._http.request(
            method="POST",
            path=f"/api/v1/keys/{key_id}/rotate",
            json={"name": name} if name else None
        )
        return CreateKeyResponse.model_validate(response)

    def update_scopes(self, key_id: int, scopes: List[str]) -> None:
        """Update API key scopes.

        Args:
            key_id: API key ID
            scopes: New scopes list
        """
        self._http.request(
            method="PATCH",
            path=f"/api/v1/keys/{key_id}/scopes",
            json={"scopes": scopes}
        )
```

### 6.3 BaseClient (Shared)

```python
# _base_client.py
from .config import ArkForgeConfig
from ._http import HTTPClient

class BaseClient:
    """Base client with shared functionality."""

    def __init__(self, config: ArkForgeConfig):
        self.config = config
        self._http = HTTPClient(config)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close HTTP clients."""
        self._http.close()
```

---

## 7. HTTP Transport Layer

Already covered in detail in Section 3.1 (HTTP Client), 3.2 (Retry Policy), and 3.3 (Rate Limiter).

**Summary**:
- ✅ httpx for sync/async HTTP
- ✅ Exponential backoff retry (3 attempts default)
- ✅ Token bucket rate limiting
- ✅ Server-guided rate limiting via headers
- ✅ Proper error mapping to SDK exceptions

---

## 8. Configuration Management

### 8.1 ArkForgeConfig

```python
# config.py
from dataclasses import dataclass
from typing import Optional
import os
import sys

@dataclass
class ArkForgeConfig:
    """ArkForge SDK configuration.

    Attributes:
        api_key: ArkForge API key (required)
        base_url: API base URL (default: http://localhost:3001)
        timeout: Request timeout in seconds (default: 60)
        retry_attempts: Max retry attempts (default: 3)
        retry_delay: Base retry delay in seconds (default: 1)
        debug: Enable debug logging (default: False)
        user_agent: Custom user agent (auto-generated if None)
    """

    api_key: str
    base_url: str = "http://localhost:3001"
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0
    debug: bool = False
    user_agent: Optional[str] = None

    def __post_init__(self):
        """Validate and initialize configuration."""
        # Validate API key format
        if not self.api_key:
            raise ValueError("api_key is required")

        if not self.api_key.startswith("sk-arkforge-"):
            raise ValueError(
                "Invalid API key format. "
                "API key must start with 'sk-arkforge-'"
            )

        # Generate user agent if not provided
        if self.user_agent is None:
            from .version import __version__
            python_version = sys.version.split()[0]
            self.user_agent = f"arkforge-python/{__version__} python/{python_version}"

        # Add version header
        from .version import __version__
        self.version = __version__

    @classmethod
    def from_env(cls, **overrides) -> "ArkForgeConfig":
        """Load configuration from environment variables.

        Environment variables:
            ARKFORGE_API_KEY: API key (required)
            ARKFORGE_BASE_URL: Base URL (optional)

        Args:
            **overrides: Config overrides

        Returns:
            ArkForgeConfig instance

        Raises:
            ValueError: If ARKFORGE_API_KEY not set

        Example:
            >>> import os
            >>> os.environ["ARKFORGE_API_KEY"] = "sk-arkforge-..."
            >>> config = ArkForgeConfig.from_env()
        """
        api_key = os.getenv("ARKFORGE_API_KEY")
        if not api_key:
            raise ValueError(
                "ARKFORGE_API_KEY environment variable not set. "
                "Please set it or pass api_key directly."
            )

        base_url = os.getenv("ARKFORGE_BASE_URL", cls.base_url)

        return cls(
            api_key=api_key,
            base_url=base_url,
            **overrides
        )
```

### 8.2 Security Features

**API Key Protection**:
```python
def __repr__(self) -> str:
    """Mask API key in repr."""
    masked_key = f"{self.api_key[:16]}..."
    return (
        f"ArkForgeConfig("
        f"api_key={masked_key}, "
        f"base_url={self.base_url}, "
        f"timeout={self.timeout})"
    )
```

---

## 9. Testing Strategy

### 9.1 Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures
├── unit/                          # Unit tests (mocked)
│   ├── test_client.py            # ArkForgeClient tests
│   ├── test_key_management.py    # KeyManagementClient tests
│   ├── test_config.py            # Config validation
│   ├── test_errors.py            # Exception hierarchy
│   ├── test_retry.py             # Retry policy logic
│   ├── test_rate_limiter.py      # Rate limiter
│   ├── test_http.py              # HTTP client
│   └── test_models.py            # Pydantic models
├── integration/                   # Integration tests (real API)
│   ├── test_portfolio_api.py    # Portfolio endpoints
│   ├── test_key_api.py           # Key management endpoints
│   └── test_error_scenarios.py  # Error handling
└── fixtures/                      # Test data
    ├── requests.json
    └── responses.json
```

### 9.2 Unit Test Examples

**conftest.py**:
```python
import pytest
from arkforge import ArkForgeClient, ArkForgeConfig

@pytest.fixture
def mock_config():
    """Mock configuration."""
    return ArkForgeConfig(
        api_key="sk-arkforge-test123",
        base_url="http://localhost:3001"
    )

@pytest.fixture
def mock_client(mock_config):
    """Mock client."""
    return ArkForgeClient(
        api_key=mock_config.api_key,
        base_url=mock_config.base_url
    )
```

**test_config.py**:
```python
import pytest
from arkforge import ArkForgeConfig

def test_config_validation():
    """Test config validation."""
    # Valid
    config = ArkForgeConfig(api_key="sk-arkforge-abc123")
    assert config.api_key == "sk-arkforge-abc123"

    # Invalid format
    with pytest.raises(ValueError, match="Invalid API key format"):
        ArkForgeConfig(api_key="invalid-key")

    # Missing key
    with pytest.raises(ValueError, match="api_key is required"):
        ArkForgeConfig(api_key="")

def test_from_env(monkeypatch):
    """Test loading from environment."""
    monkeypatch.setenv("ARKFORGE_API_KEY", "sk-arkforge-test")
    config = ArkForgeConfig.from_env()
    assert config.api_key == "sk-arkforge-test"
```

**test_retry.py**:
```python
import pytest
from arkforge._retry import RetryPolicy
from arkforge.errors import ValidationError, RateLimitError

def test_retry_on_rate_limit():
    """Test retry on rate limit error."""
    policy = RetryPolicy(max_attempts=3, base_delay=0.1)

    attempt_count = 0

    @policy.with_retry
    def failing_func():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise RateLimitError("Rate limited", retry_after=0.1)
        return "success"

    result = failing_func()
    assert result == "success"
    assert attempt_count == 3

def test_no_retry_on_validation_error():
    """Test no retry on validation error."""
    policy = RetryPolicy(max_attempts=3)

    attempt_count = 0

    @policy.with_retry
    def failing_func():
        nonlocal attempt_count
        attempt_count += 1
        raise ValidationError("Invalid params")

    with pytest.raises(ValidationError):
        failing_func()

    assert attempt_count == 1  # Only one attempt
```

### 9.3 Integration Test Examples

**test_portfolio_api.py**:
```python
import pytest
from arkforge import ArkForgeClient, OptimizePortfolioRequest

@pytest.mark.integration
def test_optimize_portfolio():
    """Test portfolio optimization (requires running API)."""
    client = ArkForgeClient(
        api_key="sk-arkforge-test",  # Test API key
        base_url="http://localhost:3001"
    )

    request = OptimizePortfolioRequest(
        assets=["BTC", "ETH", "SOL"],
        risk_profile="moderate"
    )

    result = client.optimize_portfolio(request)

    # Validate response
    assert result.allocation is not None
    assert len(result.allocation) == 3
    assert sum(result.allocation.values()) == pytest.approx(100, rel=0.1)
    assert result.expected_return > 0
    assert 0 <= result.confidence <= 1
```

### 9.4 Test Coverage Goals

| Component      | Target Coverage |
| -------------- | --------------- |
| models/        | >95%            |
| errors.py      | >90%            |
| config.py      | >90%            |
| _retry.py      | >90%            |
| _rate_limiter. | >85%            |
| _http.py       | >85%            |
| client.py      | >85%            |
| **Overall**    | **>85%**        |

---

## 10. Development Workflow

### 10.1 Project Setup

**pyproject.toml**:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "arkforge"
version = "0.1.0"
description = "Official Python SDK for ArkForge DeFi portfolio management"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.7"
keywords = ["arkforge", "defi", "portfolio", "crypto", "sdk"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "respx>=0.20.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "black>=23.9.0",
]

docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/arkforge-sdk-py"
Documentation = "https://arkforge-sdk-py.readthedocs.io"
Repository = "https://github.com/yourusername/arkforge-sdk-py"
Changelog = "https://github.com/yourusername/arkforge-sdk-py/blob/main/CHANGELOG.md"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "integration: Integration tests requiring live API",
    "unit: Unit tests with mocks",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["arkforge"]
omit = ["tests/*", "examples/*"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false

[tool.mypy]
python_version = "3.7"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py37"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line too long (handled by black)

[tool.black]
line-length = 100
target-version = ["py37", "py38", "py39", "py310", "py311", "py312"]
```

### 10.2 Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=arkforge --cov-report=html --cov-report=term

# Run only unit tests
pytest tests/unit

# Run only integration tests (requires API)
pytest tests/integration -m integration

# Type checking
mypy arkforge

# Linting
ruff check arkforge

# Formatting
black arkforge tests

# All quality checks
pytest --cov=arkforge --cov-report=term && mypy arkforge && ruff check arkforge
```

### 10.3 CI/CD Pipeline

**.github/workflows/ci.yml**:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest --cov=arkforge --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run mypy
        run: mypy arkforge

      - name: Run ruff
        run: ruff check arkforge

      - name: Run black check
        run: black --check arkforge tests
```

---

## 11. Performance Considerations

### 11.1 Connection Pooling

- httpx maintains connection pool automatically
- Reuse client instances to leverage pooling
- Close clients when done with context managers

### 11.2 Async Support

- Async methods for high-concurrency scenarios
- Use `asyncio.gather()` for parallel requests
- Example:

```python
async def optimize_multiple_portfolios(portfolios):
    client = ArkForgeClient(api_key="...")

    tasks = [
        client.optimize_portfolio_async(portfolio)
        for portfolio in portfolios
    ]

    results = await asyncio.gather(*tasks)
    return results
```

### 11.3 Request Batching

- For bulk operations, consider batching
- Respect rate limits
- Use async for parallel processing

---

## 12. Security Design

### 12.1 API Key Protection

**Storage**:
- Never hardcode API keys
- Use environment variables
- Consider keyring for desktop apps

**Logging**:
```python
def __repr__(self):
    """Mask API key in repr."""
    masked_key = f"{self.api_key[:16]}..."
    return f"ArkForgeConfig(api_key={masked_key}, ...)"
```

### 12.2 HTTPS Enforcement

- Always use HTTPS in production
- Validate SSL certificates
- No certificate bypass options

### 12.3 Request Signing (Future)

- Consider HMAC request signing for additional security
- Timestamp validation
- Nonce for replay protection

---

## Appendix A: Example Usage

### Basic Usage

```python
from arkforge import ArkForgeClient

# Initialize client
client = ArkForgeClient(api_key="sk-arkforge-...")

# Optimize portfolio
result = client.optimize_portfolio(
    assets=["BTC", "ETH", "SOL"],
    risk_profile="moderate"
)

# Print results
print(f"Allocation: {result.allocation}")
print(f"Expected Return: {result.expected_return * 100:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### Async Usage

```python
import asyncio
from arkforge import ArkForgeClient

async def main():
    client = ArkForgeClient(api_key="sk-arkforge-...")

    result = await client.optimize_portfolio_async(
        assets=["BTC", "ETH", "SOL"],
        risk_profile="moderate"
    )

    print(result.allocation)

asyncio.run(main())
```

### Error Handling

```python
from arkforge import ArkForgeClient, RateLimitError, ValidationError

client = ArkForgeClient(api_key="sk-arkforge-...")

try:
    result = client.optimize_portfolio(
        assets=["BTC", "ETH"],
        risk_profile="moderate"
    )
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
    time.sleep(e.retry_after)
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Appendix B: Design Decisions

### Why Pydantic v2?

- ✅ Best-in-class validation
- ✅ Excellent IDE support
- ✅ JSON Schema generation
- ✅ Performance (Rust-based core)
- ✅ Immutable models

### Why httpx over requests?

- ✅ Async support (httpx.AsyncClient)
- ✅ HTTP/2 support
- ✅ Modern API design
- ✅ Active development
- ✅ Full type hints

### Why Token Bucket for Rate Limiting?

- ✅ Simple and efficient
- ✅ Smooth rate limiting (not bursty)
- ✅ Thread-safe implementation
- ✅ Server-guided adaptation

### Why Exponential Backoff?

- ✅ Industry standard for retries
- ✅ Reduces server load
- ✅ Fair to other clients
- ✅ Configurable max attempts

---

## Appendix C: Future Enhancements

### Phase 2 Features

1. **Webhook Support**: Real-time portfolio updates
2. **Streaming API**: Long-running optimizations
3. **Request Caching**: Cache responses for identical requests
4. **Request Signing**: HMAC signing for additional security
5. **Batch Operations**: Optimize multiple portfolios in one call
6. **Plugin System**: Extensible middleware

### Performance Improvements

1. **Response Compression**: gzip/brotli support
2. **Connection Keep-Alive**: Persistent connections
3. **DNS Caching**: Reduce DNS lookup overhead
4. **Circuit Breaker**: Fail fast on degraded service

---

**End of Design Document**

This design provides a solid foundation for a world-class Python SDK. The architecture is modular, testable, and follows industry best practices. Ready for implementation!
