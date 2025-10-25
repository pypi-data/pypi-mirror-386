"""Unit tests for data models."""

import pytest
from arkforge.models import (
    OptimizePortfolioRequest,
    OptimizationConfig,
    Constraints,
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
