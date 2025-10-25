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
- `optimize_portfolio(request)` - Optimize portfolio allocation
- `optimize_portfolio_async(request)` - Async version
- `get_risk_profiles()` - Get available risk profiles
- `health()` - Check service health

**KeyManagementClient**:
- `create_key(request)` - Create API key
- `list_keys()` - List API keys
- `get_key_details(key_id)` - Get key details
- `revoke_key(key_id, reason)` - Revoke API key
- `rotate_key(key_id, name)` - Rotate API key

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
