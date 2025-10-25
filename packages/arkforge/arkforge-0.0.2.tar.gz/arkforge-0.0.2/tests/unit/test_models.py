"""Unit tests for data models."""

import pytest
from arkforge.models import (
    Constraints,
    HistoricalPriceData,
    HistoricalSentimentData,
    OptimizationConfig,
    OptimizePortfolioRequest,
    Options,
    PortfolioRecommendation,
)


def test_optimize_portfolio_request_valid():
    """Test valid portfolio optimization request."""
    request = OptimizePortfolioRequest(
        assets=["BTC", "ETH", "SOL"], risk_profile="moderate", horizon_days=30
    )
    assert request.assets == ["BTC", "ETH", "SOL"]
    assert request.risk_profile == "moderate"
    assert request.horizon_days == 30


def test_optimize_portfolio_request_validation():
    """Test portfolio request validation."""
    # Empty assets should fail (Pydantic ValidationError, not ValueError)
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        OptimizePortfolioRequest(assets=[], risk_profile="moderate")


def test_optimize_portfolio_request_asset_normalization():
    """Test asset symbols are normalized to uppercase."""
    request = OptimizePortfolioRequest(assets=["btc", "eth", "sol"], risk_profile="moderate")
    assert request.assets == ["BTC", "ETH", "SOL"]


def test_optimization_config():
    """Test optimization configuration."""
    config = OptimizationConfig(target_sharpe_ratio=1.5, max_volatility=0.25, goal="sharpe")
    assert config.target_sharpe_ratio == 1.5
    assert config.max_volatility == 0.25
    assert config.goal == "sharpe"


def test_constraints():
    """Test portfolio constraints."""
    constraints = Constraints(max_position_size=30.0, min_diversification=3)
    assert constraints.max_position_size == 30.0
    assert constraints.min_diversification == 3


def test_options():
    """Test request options."""
    options = Options(llm_provider="claude")
    assert options.llm_provider == "claude"


def test_options_grok():
    """Test request options with grok."""
    options = Options(llm_provider="grok")
    assert options.llm_provider == "grok"


def test_model_serialization():
    """Test model serialization with aliases."""
    request = OptimizePortfolioRequest(
        assets=["BTC", "ETH"], risk_profile="aggressive", horizon_days=7
    )
    data = request.model_dump(by_alias=True)

    # Check camelCase conversion
    assert "riskProfile" in data
    assert "horizonDays" in data
    assert data["riskProfile"] == "aggressive"
    assert data["horizonDays"] == 7


# Backtesting Models Tests


def test_historical_price_data_valid():
    """Test valid historical price data."""
    data = HistoricalPriceData(
        symbol="BTC", timestamp="2024-01-01T00:00:00Z", price=42350.50, volume=28500000.0
    )
    assert data.symbol == "BTC"
    assert data.timestamp == "2024-01-01T00:00:00Z"
    assert data.price == 42350.50
    assert data.volume == 28500000.0


def test_historical_price_data_without_volume():
    """Test historical price data without volume."""
    data = HistoricalPriceData(symbol="ETH", timestamp="2024-01-01T00:00:00Z", price=2250.30)
    assert data.symbol == "ETH"
    assert data.price == 2250.30
    assert data.volume is None


def test_historical_price_data_validation():
    """Test historical price data validation."""
    from pydantic import ValidationError

    # Price must be positive
    with pytest.raises(ValidationError) as exc_info:
        HistoricalPriceData(symbol="BTC", timestamp="2024-01-01T00:00:00Z", price=0.0)
    assert "greater than 0" in str(exc_info.value).lower()

    # Negative price should fail
    with pytest.raises(ValidationError):
        HistoricalPriceData(symbol="BTC", timestamp="2024-01-01T00:00:00Z", price=-100.0)


def test_historical_price_data_immutable():
    """Test historical price data is immutable."""
    data = HistoricalPriceData(symbol="BTC", timestamp="2024-01-01T00:00:00Z", price=42350.50)
    with pytest.raises(Exception):  # Pydantic frozen model raises ValidationError
        data.price = 50000.0


def test_historical_sentiment_data_valid():
    """Test valid historical sentiment data."""
    data = HistoricalSentimentData(
        asset="BTC",
        timestamp="2024-01-15T00:00:00Z",
        score=0.37,
        category="bullish",
        confidence=0.82,
        galaxy_score=68.5,
        alt_rank=1,
        social={"twitter_mentions": 15000},
    )
    assert data.asset == "BTC"
    assert data.score == 0.37
    assert data.category == "bullish"
    assert data.confidence == 0.82
    assert data.galaxy_score == 68.5
    assert data.alt_rank == 1
    assert data.social == {"twitter_mentions": 15000}


def test_historical_sentiment_data_minimal():
    """Test historical sentiment data with only required fields."""
    data = HistoricalSentimentData(
        asset="ETH",
        timestamp="2024-01-15T00:00:00Z",
        score=-0.25,
        category="bearish",
        confidence=0.65,
    )
    assert data.asset == "ETH"
    assert data.score == -0.25
    assert data.category == "bearish"
    assert data.galaxy_score is None
    assert data.alt_rank is None
    assert data.social is None


def test_historical_sentiment_data_score_validation():
    """Test sentiment score range validation."""
    from pydantic import ValidationError

    # Score must be between -1 and 1
    with pytest.raises(ValidationError):
        HistoricalSentimentData(
            asset="BTC",
            timestamp="2024-01-15T00:00:00Z",
            score=1.5,  # Invalid: > 1
            category="bullish",
            confidence=0.8,
        )

    with pytest.raises(ValidationError):
        HistoricalSentimentData(
            asset="BTC",
            timestamp="2024-01-15T00:00:00Z",
            score=-1.5,  # Invalid: < -1
            category="bearish",
            confidence=0.8,
        )


def test_historical_sentiment_data_confidence_validation():
    """Test confidence range validation."""
    from pydantic import ValidationError

    # Confidence must be between 0 and 1
    with pytest.raises(ValidationError):
        HistoricalSentimentData(
            asset="BTC",
            timestamp="2024-01-15T00:00:00Z",
            score=0.5,
            category="bullish",
            confidence=1.5,  # Invalid: > 1
        )


def test_historical_sentiment_data_category_validation():
    """Test category literal validation."""
    from pydantic import ValidationError

    # Category must be one of the valid literals
    with pytest.raises(ValidationError):
        HistoricalSentimentData(
            asset="BTC",
            timestamp="2024-01-15T00:00:00Z",
            score=0.5,
            category="super_bullish",  # Invalid category
            confidence=0.8,
        )


def test_historical_sentiment_data_galaxy_score_validation():
    """Test galaxy score range validation."""
    from pydantic import ValidationError

    # Galaxy score must be between 0 and 100
    with pytest.raises(ValidationError):
        HistoricalSentimentData(
            asset="BTC",
            timestamp="2024-01-15T00:00:00Z",
            score=0.5,
            category="bullish",
            confidence=0.8,
            galaxy_score=150.0,  # Invalid: > 100
        )


def test_historical_sentiment_data_alt_rank_validation():
    """Test alt rank range validation."""
    from pydantic import ValidationError

    # Alt rank must be between 1 and 4000
    with pytest.raises(ValidationError):
        HistoricalSentimentData(
            asset="BTC",
            timestamp="2024-01-15T00:00:00Z",
            score=0.5,
            category="bullish",
            confidence=0.8,
            alt_rank=5000,  # Invalid: > 4000
        )


def test_historical_sentiment_data_alias_serialization():
    """Test camelCase alias serialization for sentiment data."""
    data = HistoricalSentimentData(
        asset="BTC",
        timestamp="2024-01-15T00:00:00Z",
        score=0.5,
        category="bullish",
        confidence=0.8,
        galaxy_score=68.5,
        alt_rank=1,
    )
    serialized = data.model_dump(by_alias=True)

    # Check camelCase conversion
    assert "galaxyScore" in serialized
    assert "altRank" in serialized
    assert serialized["galaxyScore"] == 68.5
    assert serialized["altRank"] == 1


def test_optimize_portfolio_request_with_historical_data():
    """Test portfolio request with historical data for backtesting."""
    historical_data = [
        {"symbol": "BTC", "timestamp": "2024-01-01T00:00:00Z", "price": 42350.50},
        {"symbol": "BTC", "timestamp": "2024-01-02T00:00:00Z", "price": 43120.75},
    ]

    request = OptimizePortfolioRequest(
        assets=["BTC", "ETH"], risk_profile="moderate", historical_data=historical_data
    )

    assert request.assets == ["BTC", "ETH"]
    assert request.historical_data == historical_data
    assert request.historical_sentiment is None


def test_optimize_portfolio_request_with_historical_sentiment():
    """Test portfolio request with historical sentiment data."""
    historical_sentiment = [
        {
            "asset": "BTC",
            "timestamp": "2024-01-15T00:00:00Z",
            "score": 0.37,
            "category": "bullish",
            "confidence": 0.82,
        }
    ]

    request = OptimizePortfolioRequest(
        assets=["BTC"],
        risk_profile="moderate",
        historical_data=[{"symbol": "BTC", "timestamp": "2024-01-01T00:00:00Z", "price": 42350.50}],
        historical_sentiment=historical_sentiment,
    )

    assert request.historical_sentiment == historical_sentiment


def test_optimize_portfolio_request_backtest_serialization():
    """Test serialization of portfolio request with historical data."""
    request = OptimizePortfolioRequest(
        assets=["BTC"],
        risk_profile="moderate",
        historical_data=[{"symbol": "BTC", "timestamp": "2024-01-01T00:00:00Z", "price": 42350.50}],
        historical_sentiment=[
            {
                "asset": "BTC",
                "timestamp": "2024-01-15T00:00:00Z",
                "score": 0.5,
                "category": "bullish",
                "confidence": 0.8,
            }
        ],
    )

    serialized = request.model_dump(by_alias=True)

    # Check camelCase aliases for backtesting fields
    assert "historicalData" in serialized
    assert "historicalSentiment" in serialized
    assert serialized["historicalData"][0]["symbol"] == "BTC"
    assert serialized["historicalSentiment"][0]["asset"] == "BTC"


def test_optimize_portfolio_request_backward_compatibility():
    """Test that historical fields are optional for backward compatibility."""
    # Should work without historical data (live mode)
    request = OptimizePortfolioRequest(assets=["BTC", "ETH"], risk_profile="moderate")

    assert request.historical_data is None
    assert request.historical_sentiment is None

    # Serialization should exclude None values
    serialized = request.model_dump(exclude_none=True)
    assert "historical_data" not in serialized
    assert "historical_sentiment" not in serialized
