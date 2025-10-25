"""Backtesting example with historical data.

This example demonstrates how to use the SDK for backtesting by providing
historical price data instead of fetching live data.
"""

from arkforge import ArkForgeClient, OptimizePortfolioRequest

# Initialize client (same as live mode)
client = ArkForgeClient(api_key="sk-arkforge-your-api-key")

# Prepare historical price data (90+ days per asset)
historical_data = [
    # BTC historical data
    {"symbol": "BTC", "timestamp": "2024-01-01T00:00:00Z", "price": 42350.50, "volume": 28500000},
    {"symbol": "BTC", "timestamp": "2024-01-02T00:00:00Z", "price": 43120.75, "volume": 29100000},
    {"symbol": "BTC", "timestamp": "2024-01-03T00:00:00Z", "price": 42890.25, "volume": 27800000},
    # ... continue with 90+ days of BTC data
    # ETH historical data
    {"symbol": "ETH", "timestamp": "2024-01-01T00:00:00Z", "price": 2250.30, "volume": 15200000},
    {"symbol": "ETH", "timestamp": "2024-01-02T00:00:00Z", "price": 2305.80, "volume": 16100000},
    {"symbol": "ETH", "timestamp": "2024-01-03T00:00:00Z", "price": 2280.45, "volume": 15800000},
    # ... continue with 90+ days of ETH data
    # SOL historical data
    {"symbol": "SOL", "timestamp": "2024-01-01T00:00:00Z", "price": 98.50, "volume": 5400000},
    {"symbol": "SOL", "timestamp": "2024-01-02T00:00:00Z", "price": 102.30, "volume": 5900000},
    {"symbol": "SOL", "timestamp": "2024-01-03T00:00:00Z", "price": 99.75, "volume": 5600000},
    # ... continue with 90+ days of SOL data
]

# Optional: Historical sentiment data
historical_sentiment = [
    {
        "asset": "BTC",
        "timestamp": "2024-01-15T00:00:00Z",
        "score": 0.37,
        "category": "bullish",
        "confidence": 0.82,
        "galaxyScore": 68.5,
        "altRank": 1,
    },
    {
        "asset": "ETH",
        "timestamp": "2024-01-15T00:00:00Z",
        "score": 0.29,
        "category": "bullish",
        "confidence": 0.75,
        "galaxyScore": 65.2,
        "altRank": 2,
    },
    {
        "asset": "SOL",
        "timestamp": "2024-01-15T00:00:00Z",
        "score": 0.42,
        "category": "bullish",
        "confidence": 0.78,
        "galaxyScore": 62.8,
        "altRank": 5,
    },
]

# Create backtest request (same interface as live mode, just add historical data)
request = OptimizePortfolioRequest(
    assets=["BTC", "ETH", "SOL"],
    risk_profile="moderate",
    horizon_days=7,
    # NEW: Add historical data for backtesting
    historical_data=historical_data,
    historical_sentiment=historical_sentiment,  # Optional
)

# Execute backtest (API automatically detects backtest mode from historical_data)
result = client.optimize_portfolio(request)

# Results are identical to live mode
print("=== Backtest Results ===")
print(f"\nRecommended Allocation:")
for asset, percentage in result.allocation.items():
    print(f"  {asset}: {percentage:.2f}%")

print(f"\nExpected Return: {result.expected_return * 100:.2f}%")
print(f"Expected Volatility: {result.expected_volatility * 100:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Confidence: {result.confidence * 100:.2f}%")

print(f"\nRecommended Actions:")
for action in result.actions:
    print(
        f"  {action.action.upper()} {action.symbol}: "
        f"{action.current_percentage:.2f}% → {action.target_percentage:.2f}% "
        f"(change: {action.change:+.2f}%)"
    )

if result.rationale:
    print(f"\nRationale:")
    print(f"  Market Context: {result.rationale.market_context}")
    print(f"  Forecast Insights: {result.rationale.forecast_insights}")
    if result.rationale.sentiment_insights:
        print(f"  Sentiment Insights: {result.rationale.sentiment_insights}")
