# ArkForge Python SDK

Python client for ArkForge DeFi portfolio management API.

[![PyPI version](https://badge.fury.io/py/arkforge.svg)](https://badge.fury.io/py/arkforge)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)

## Installation

```bash
pip install arkforge
```

## Requirements

- Python 3.8+
- Valid ArkForge API key

## Usage

```python
from arkforge import ArkForgeClient
from arkforge.models import OptimizePortfolioRequest

client = ArkForgeClient(api_key="sk-arkforge-...")

result = client.optimize_portfolio(
    OptimizePortfolioRequest(
        assets=["BTC", "ETH", "SOL"],
        risk_profile="moderate"
    )
)

print(result.allocation)
```

## Configuration

```python
client = ArkForgeClient(
    api_key="sk-arkforge-...",
    base_url="https://api.arkforge.io",
    timeout=120,
    retry_attempts=5
)
```

Environment variables:
- `ARKFORGE_API_KEY` - API key
- `ARKFORGE_BASE_URL` - API base URL (default: http://localhost:3001)

## API Methods

**ArkForgeClient**:
- `optimize_portfolio(request)` - Optimize portfolio allocation (live or backtest mode)
- `optimize_portfolio_async(request)` - Async version
- `get_risk_profiles()` - Get available risk profiles
- `health()` - Check service health

**KeyManagementClient**:
- `create_key(request)` - Create API key
- `list_keys()` - List API keys
- `get_key_details(key_id)` - Get key details
- `revoke_key(key_id, reason)` - Revoke API key
- `rotate_key(key_id, name)` - Rotate API key

## Backtesting

The SDK supports backtesting by providing historical price data. The API automatically enters backtest mode when `historical_data` is provided.

```python
from arkforge import ArkForgeClient, OptimizePortfolioRequest

client = ArkForgeClient(api_key="sk-arkforge-...")

# Prepare historical data (90+ days per asset)
historical_data = [
    {"symbol": "BTC", "timestamp": "2024-01-01T00:00:00Z", "price": 42350.50},
    {"symbol": "BTC", "timestamp": "2024-01-02T00:00:00Z", "price": 43120.75},
    # ... 90+ days of data per asset
]

# Optional: Historical sentiment data
historical_sentiment = [
    {
        "asset": "BTC",
        "timestamp": "2024-01-15T00:00:00Z",
        "score": 0.37,
        "category": "bullish",
        "confidence": 0.82
    }
]

# Same request interface, just add historical data
request = OptimizePortfolioRequest(
    assets=["BTC", "ETH", "SOL"],
    risk_profile="moderate",
    historical_data=historical_data,
    historical_sentiment=historical_sentiment  # Optional
)

result = client.optimize_portfolio(request)
```

See `examples/backtesting_example.py` for a complete example.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy arkforge

# Linting
ruff check arkforge
```
