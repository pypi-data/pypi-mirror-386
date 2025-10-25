"""Basic usage example for ArkForge SDK."""

from arkforge import ArkForgeClient
from arkforge.models import OptimizePortfolioRequest


def main():
    """Basic portfolio optimization example."""
    # Initialize client with API key
    client = ArkForgeClient(api_key="sk-arkforge-your-key-here")

    # Create optimization request
    request = OptimizePortfolioRequest(
        assets=["BTC", "ETH", "SOL"],
        risk_profile="moderate",
        horizon_days=7
    )

    # Optimize portfolio
    print("Optimizing portfolio...")
    result = client.optimize_portfolio(request)

    # Print results
    print("\n=== Portfolio Recommendation ===")
    print(f"\nAllocation:")
    for symbol, percentage in result.allocation.items():
        print(f"  {symbol}: {percentage:.1f}%")

    print(f"\nMetrics:")
    print(f"  Expected Return: {result.expected_return * 100:.2f}%")
    print(f"  Expected Volatility: {result.expected_volatility * 100:.2f}%")
    print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"  Confidence: {result.confidence * 100:.0f}%")

    # Print actions
    if result.actions:
        print(f"\nRecommended Actions:")
        for action in result.actions:
            print(f"  {action.action.upper()} {action.symbol}: {action.change:+.1f}%")

    # Clean up
    client.close()


if __name__ == "__main__":
    main()
