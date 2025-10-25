"""ArkForge Python SDK.

Official Python SDK for ArkForge DeFi portfolio management service.

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

from .client import ArkForgeClient
from .config import ArkForgeConfig
from .errors import (
    ArkForgeError,
    AuthenticationError,
    ConnectionError,
    DNSError,
    ExpiredApiKeyError,
    ForecastFailedError,
    InvalidApiKeyError,
    InvalidAssetsError,
    InvalidParametersError,
    InvalidRiskProfileError,
    NetworkError,
    RateLimitError,
    SentimentFailedError,
    ServiceError,
    SynthesisFailedError,
    TimeoutError,
    ValidationError,
)
from .key_management import KeyManagementClient
from .models import (
    Action,
    ActionType,
    ApiKeyDetails,
    ApiKeyInfo,
    Constraints,
    CreateKeyRequest,
    CreateKeyResponse,
    HealthStatus,
    HealthStatusType,
    LLMProvider,
    Metadata,
    OptimizationConfig,
    OptimizationGoal,
    OptimizePortfolioRequest,
    PortfolioRecommendation,
    Rationale,
    RiskProfile,
    RiskProfileType,
    SwapInstruction,
)
from .version import __version__

__all__ = [
    # Version
    "__version__",
    # Clients
    "ArkForgeClient",
    "KeyManagementClient",
    # Configuration
    "ArkForgeConfig",
    # Request models
    "OptimizePortfolioRequest",
    "OptimizationConfig",
    "Constraints",
    "CreateKeyRequest",
    # Response models
    "PortfolioRecommendation",
    "Action",
    "SwapInstruction",
    "Rationale",
    "Metadata",
    "RiskProfile",
    "CreateKeyResponse",
    "ApiKeyInfo",
    "ApiKeyDetails",
    "HealthStatus",
    # Enums
    "RiskProfileType",
    "ActionType",
    "OptimizationGoal",
    "HealthStatusType",
    "LLMProvider",
    # Exceptions
    "ArkForgeError",
    "ValidationError",
    "InvalidParametersError",
    "InvalidRiskProfileError",
    "InvalidAssetsError",
    "AuthenticationError",
    "InvalidApiKeyError",
    "ExpiredApiKeyError",
    "RateLimitError",
    "TimeoutError",
    "ServiceError",
    "ForecastFailedError",
    "SentimentFailedError",
    "SynthesisFailedError",
    "NetworkError",
    "ConnectionError",
    "DNSError",
]
