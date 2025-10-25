"""Response models for ArkForge API."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .common import ActionType, HealthStatusType


class Action(BaseModel):
    """Portfolio action recommendation.

    Attributes:
        action: Type of action (buy, sell, hold)
        symbol: Asset symbol
        target_percentage: Recommended allocation percentage
        current_percentage: Current allocation percentage
        change: Change in percentage points
    """

    action: ActionType
    symbol: str
    target_percentage: float = Field(..., alias="targetPercentage", ge=0, le=100)
    current_percentage: float = Field(..., alias="currentPercentage", ge=0, le=100)
    change: float = Field(..., ge=-100, le=100)

    model_config = {"frozen": True, "populate_by_name": True}


class SwapInstruction(BaseModel):
    """Token swap instruction.

    Attributes:
        type: Instruction type (always "swap")
        from_token: Token to swap from
        from_amount: Amount to swap from
        to_token: Token to swap to
        to_amount: Amount to receive
        reason: Reason for swap
    """

    type: str = "swap"
    from_token: str = Field(..., alias="fromToken")
    from_amount: float = Field(..., alias="fromAmount")
    to_token: str = Field(..., alias="toToken")
    to_amount: float = Field(..., alias="toAmount")
    reason: str

    model_config = {"frozen": True, "populate_by_name": True}


class Rationale(BaseModel):
    """Optimization rationale and insights.

    Attributes:
        drivers: Key drivers of the recommendation
        risks: Identified risks and concerns
        market_context: Current market context
        forecast_insights: Insights from price forecasts
        sentiment_insights: Insights from sentiment analysis
    """

    drivers: List[str]
    risks: List[str]
    market_context: str = Field(..., alias="marketContext")
    forecast_insights: str = Field(..., alias="forecastInsights")
    sentiment_insights: str = Field(..., alias="sentimentInsights")

    model_config = {"frozen": True, "populate_by_name": True}


class Metadata(BaseModel):
    """Response metadata.

    Attributes:
        workflow_id: Workflow execution ID
        timestamp: Response timestamp
        processing_time: Processing time in milliseconds
        llm_provider: LLM provider used
        llm_model: LLM model used
        request_id: Request ID for support
    """

    workflow_id: str = Field(..., alias="workflowId")
    timestamp: datetime
    processing_time: int = Field(..., alias="processingTime", description="Processing time in ms")
    llm_provider: str = Field(..., alias="llmProvider")
    llm_model: str = Field(..., alias="llmModel")
    request_id: str = Field(..., alias="requestId")

    model_config = {"frozen": True, "populate_by_name": True}


class PortfolioRecommendation(BaseModel):
    """Portfolio optimization recommendation.

    This is the main response from portfolio optimization requests.

    Example:
        >>> recommendation = PortfolioRecommendation.model_validate(response_data)
        >>> print(recommendation.allocation)
        {'BTC': 40.0, 'ETH': 35.0, 'SOL': 25.0}
        >>> print(f"Sharpe Ratio: {recommendation.sharpe_ratio:.2f}")
        Sharpe Ratio: 1.45
    """

    # Allocation
    allocation: Dict[str, float] = Field(..., description="Recommended allocation percentages")

    # Metrics
    expected_return: float = Field(
        ..., alias="expectedReturn", description="Annualized expected return (0.15 = 15%)"
    )
    expected_volatility: float = Field(
        ..., alias="expectedVolatility", description="Annualized volatility (0.25 = 25%)"
    )
    sharpe_ratio: float = Field(..., alias="sharpeRatio", description="Risk-adjusted return metric")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in recommendation (0-1)")

    # Actions
    actions: List[Action]
    swaps: Optional[List[SwapInstruction]] = None

    # Rationale (optional, depends on request)
    rationale: Optional[Rationale] = None

    # Metadata (optional)
    metadata: Optional[Metadata] = None

    model_config = {"frozen": True, "populate_by_name": True}


class RiskProfile(BaseModel):
    """Risk profile description.

    Attributes:
        name: Profile name
        description: Profile description
        target_volatility: Target volatility range
        max_drawdown: Maximum acceptable drawdown
        expected_return: Expected return range
        asset_preferences: Preferred asset types
    """

    name: str
    description: str
    target_volatility: str = Field(..., alias="targetVolatility")
    max_drawdown: str = Field(..., alias="maxDrawdown")
    expected_return: str = Field(..., alias="expectedReturn")
    asset_preferences: List[str] = Field(..., alias="assetPreferences")

    model_config = {"frozen": True, "populate_by_name": True}


class CreateKeyResponse(BaseModel):
    """API key creation response.

    WARNING: The full api_key is only shown once! Store it securely.

    Attributes:
        api_key: Full API key (shown only once!)
        key_id: Numeric key ID
        prefix: Key prefix (first 16 characters)
        warning: Security warning message
    """

    api_key: str = Field(..., alias="apiKey", description="Full API key (shown once!)")
    key_id: int = Field(..., alias="keyId")
    prefix: str = Field(..., description="Key prefix (first 16 chars)")
    warning: str = "This API key will only be shown once. Store it securely."

    model_config = {"frozen": True, "populate_by_name": True}


class ApiKeyInfo(BaseModel):
    """API key information (without full key).

    Attributes:
        id: Key ID
        prefix: Key prefix
        name: Key name
        scopes: Key scopes
        created_at: Creation timestamp
        last_used_at: Last usage timestamp
        expires_at: Expiration timestamp
        is_active: Whether key is active
    """

    id: int
    prefix: str
    name: str
    scopes: List[str]
    created_at: datetime = Field(..., alias="createdAt")
    last_used_at: Optional[datetime] = Field(None, alias="lastUsedAt")
    expires_at: datetime = Field(..., alias="expiresAt")
    is_active: bool = Field(..., alias="isActive")

    model_config = {"frozen": True, "populate_by_name": True}


class ApiKeyUsage(BaseModel):
    """API key usage statistics.

    Attributes:
        total_requests: Total requests made
        successful_requests: Successful requests
        failed_requests: Failed requests
        last_request_at: Timestamp of last request
        average_duration: Average request duration in ms
    """

    total_requests: int = Field(..., alias="totalRequests")
    successful_requests: int = Field(..., alias="successfulRequests")
    failed_requests: int = Field(..., alias="failedRequests")
    last_request_at: Optional[datetime] = Field(None, alias="lastRequestAt")
    average_duration: float = Field(..., alias="averageDuration")

    model_config = {"frozen": True, "populate_by_name": True}


class ApiKeyDetails(ApiKeyInfo):
    """Detailed API key information with usage stats.

    Inherits from ApiKeyInfo and adds usage statistics.
    """

    usage: ApiKeyUsage

    model_config = {"frozen": True, "populate_by_name": True}


class ServiceStatus(BaseModel):
    """Individual service status.

    Attributes:
        status: Service status (ok, degraded, unknown)
    """

    status: str

    model_config = {"frozen": True, "populate_by_name": True}


class HealthStatus(BaseModel):
    """Service health status.

    Attributes:
        status: Overall status
        timestamp: Status timestamp
        uptime: Service uptime in seconds
        services: Individual service statuses
    """

    status: HealthStatusType
    timestamp: datetime
    uptime: float
    services: Dict[str, str]

    model_config = {"frozen": True, "populate_by_name": True}
