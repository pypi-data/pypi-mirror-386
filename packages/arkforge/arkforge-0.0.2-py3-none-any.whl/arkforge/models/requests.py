"""Request models for ArkForge API."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from .common import OptimizationGoal, RiskProfileType


class OptimizationConfig(BaseModel):
    """Portfolio optimization configuration.

    Attributes:
        target_sharpe_ratio: Target Sharpe ratio to achieve
        max_volatility: Maximum acceptable volatility (0-1)
        min_expected_return: Minimum expected return (0-1)
        goal: Primary optimization goal
        sentiment_weight: Weight for sentiment analysis (0-1)
        ignore_sentiment: Whether to ignore sentiment completely
        optimistic_bias: Apply optimistic bias to forecasts
        llm_provider: LLM provider to use (openai, anthropic, xai, mistral)
        llm_model: Specific LLM model to use
    """

    target_sharpe_ratio: Optional[float] = Field(
        None, alias="targetSharpeRatio", ge=0, description="Target Sharpe ratio"
    )
    max_volatility: Optional[float] = Field(
        None, alias="maxVolatility", ge=0, le=1, description="Max volatility (0-1)"
    )
    min_expected_return: Optional[float] = Field(
        None, alias="minExpectedReturn", ge=0, le=1, description="Min expected return (0-1)"
    )
    goal: Optional[OptimizationGoal] = Field(None, description="Optimization goal")
    sentiment_weight: Optional[float] = Field(
        1.0, alias="sentimentWeight", ge=0, le=1, description="Sentiment weight (0-1)"
    )
    ignore_sentiment: Optional[bool] = Field(
        False, alias="ignoreSentiment", description="Ignore sentiment analysis"
    )
    optimistic_bias: Optional[bool] = Field(
        False, alias="optimisticBias", description="Apply optimistic bias"
    )

    model_config = {"frozen": True, "populate_by_name": True}


class Options(BaseModel):
    """Request options.

    Attributes:
        llm_provider: LLM provider to use - just "claude" or "grok"
    """

    llm_provider: Optional[str] = Field(
        None, alias="llmProvider", description="LLM provider (claude or grok)"
    )

    model_config = {"frozen": True, "populate_by_name": True}


class Constraints(BaseModel):
    """Portfolio constraints.

    Attributes:
        max_position_size: Maximum percentage per asset (0-100)
        min_diversification: Minimum number of different assets
        excluded_assets: Asset symbols to exclude from portfolio
    """

    max_position_size: Optional[float] = Field(
        None, alias="maxPositionSize", ge=0, le=100, description="Max % per asset"
    )
    min_diversification: Optional[int] = Field(
        None, alias="minDiversification", ge=1, description="Min number of assets"
    )
    excluded_assets: Optional[List[str]] = Field(
        None, alias="excludedAssets", description="Assets to exclude"
    )

    model_config = {"frozen": True, "populate_by_name": True}


class HistoricalPriceData(BaseModel):
    """Historical price data point for backtesting.

    Attributes:
        symbol: Asset symbol (e.g., BTC, ETH)
        timestamp: ISO 8601 timestamp
        price: Price in USD
        volume: Trading volume (optional)
    """

    symbol: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    price: float = Field(..., gt=0, description="Price in USD")
    volume: Optional[float] = Field(None, description="Trading volume")

    model_config = {"frozen": True}


class HistoricalSentimentData(BaseModel):
    """Historical sentiment data point for backtesting.

    Attributes:
        asset: Asset symbol
        timestamp: ISO 8601 timestamp
        score: Sentiment score (-1 to +1)
        category: Sentiment category
        confidence: Confidence level (0-1)
        galaxy_score: LunarCrush Galaxy Score (0-100, optional)
        alt_rank: LunarCrush AltRank (1-4000, optional)
        social: Social metrics (optional)
    """

    asset: str = Field(..., description="Asset symbol")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    score: float = Field(..., ge=-1, le=1, description="Sentiment score (-1 to +1)")
    category: Literal["very_bearish", "bearish", "neutral", "bullish", "very_bullish"] = Field(
        ..., description="Sentiment category"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence (0-1)")
    galaxy_score: Optional[float] = Field(
        None, alias="galaxyScore", ge=0, le=100, description="LunarCrush Galaxy Score"
    )
    alt_rank: Optional[int] = Field(
        None, alias="altRank", ge=1, le=4000, description="LunarCrush AltRank"
    )
    social: Optional[Dict[str, Any]] = Field(None, description="Social metrics")

    model_config = {"frozen": True, "populate_by_name": True}


class OptimizePortfolioRequest(BaseModel):
    """Request to optimize portfolio allocation.

    Example:
        >>> request = OptimizePortfolioRequest(
        ...     assets=["BTC", "ETH", "SOL"],
        ...     risk_profile="moderate",
        ...     horizon_days=30
        ... )
    """

    # Required fields
    assets: List[str] = Field(..., min_length=1, description="Asset symbols (e.g., BTC, ETH)")
    risk_profile: RiskProfileType = Field(
        ..., alias="riskProfile", description="Risk profile (conservative, moderate, aggressive)"
    )

    # Optional fields
    current_portfolio: Optional[Dict[str, float]] = Field(
        None, alias="currentPortfolio", description="Current allocation percentages"
    )
    budget: Optional[float] = Field(None, gt=0, description="Investment budget")
    horizon_days: Optional[int] = Field(
        7, alias="horizonDays", ge=1, le=365, description="Forecast horizon in days"
    )
    sentiment_timeframe_hours: Optional[int] = Field(
        168,
        alias="sentimentTimeframeHours",
        ge=1,
        description="Sentiment analysis timeframe in hours",
    )

    # Historical data for backtesting (NEW)
    historical_data: Optional[List[Dict[str, Any]]] = Field(
        None,
        alias="historicalData",
        description="Historical price data for backtesting (90+ days per asset). "
        "When provided, API operates in backtest mode using this data instead of live prices.",
    )
    historical_sentiment: Optional[List[Dict[str, Any]]] = Field(
        None,
        alias="historicalSentiment",
        description="Historical sentiment data for backtesting (optional). "
        "Provides sentiment scores aligned with historical price data.",
    )

    # Nested configurations
    constraints: Optional[Constraints] = None
    optimization: Optional[OptimizationConfig] = None
    options: Optional[Options] = None

    @field_validator("assets")
    @classmethod
    def validate_assets(cls, v: List[str]) -> List[str]:
        """Validate and normalize asset symbols."""
        if not v:
            raise ValueError("At least one asset is required")

        # Convert to uppercase for consistency
        return [asset.upper().strip() for asset in v]

    @field_validator("current_portfolio")
    @classmethod
    def validate_portfolio(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate portfolio percentages sum to 100."""
        if v is None:
            return v

        total = sum(v.values())
        # Allow small floating point errors (99.9-100.1)
        if not (99.9 <= total <= 100.1):
            raise ValueError(f"Portfolio percentages must sum to 100, got {total:.2f}")

        # Normalize to uppercase keys
        return {k.upper(): val for k, val in v.items()}

    model_config = {"frozen": True, "populate_by_name": True}


class CreateKeyRequest(BaseModel):
    """Request to create new API key.

    Example:
        >>> request = CreateKeyRequest(
        ...     name="Production Key",
        ...     expires_in_days=90,
        ...     scopes=["read", "write"]
        ... )
    """

    name: str = Field(..., min_length=1, max_length=100, description="Descriptive name for the key")
    expires_in_days: Optional[int] = Field(
        365, alias="expiresInDays", ge=1, le=365, description="Days until key expires"
    )
    scopes: Optional[List[str]] = Field(None, description="Key scopes (e.g., read, write, admin)")

    model_config = {"frozen": True, "populate_by_name": True}
