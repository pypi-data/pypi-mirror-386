"""ArkForge portfolio optimization client."""

from typing import Any, List

from ._base_client import BaseClient
from .config import ArkForgeConfig
from .models import (
    HealthStatus,
    OptimizePortfolioRequest,
    PortfolioRecommendation,
    RiskProfile,
)


class ArkForgeClient(BaseClient):
    """ArkForge portfolio optimization client.

    This is the main client for portfolio optimization operations.
    It provides methods for optimizing portfolios, getting risk profiles,
    and checking service health.

    Example:
        >>> from arkforge import ArkForgeClient
        >>> client = ArkForgeClient(api_key="sk-arkforge-...")
        >>>
        >>> # Optimize portfolio
        >>> result = client.optimize_portfolio(
        ...     OptimizePortfolioRequest(
        ...         assets=["BTC", "ETH", "SOL"],
        ...         risk_profile="moderate"
        ...     )
        ... )
        >>> print(result.allocation)
        {'BTC': 40.0, 'ETH': 35.0, 'SOL': 25.0}
        >>>
        >>> # Get risk profiles
        >>> profiles = client.get_risk_profiles()
        >>> for profile in profiles:
        ...     print(f"{profile.name}: {profile.description}")
    """

    def __init__(
        self, api_key: str, base_url: str = "http://localhost:3001", **kwargs: Any
    ) -> None:
        """Initialize ArkForge client.

        Args:
            api_key: ArkForge API key (starts with 'sk-arkforge-')
            base_url: API base URL (default: http://localhost:3001)
            **kwargs: Additional config options (timeout, retry_attempts, etc.)

        Example:
            >>> client = ArkForgeClient(
            ...     api_key="sk-arkforge-abc123",
            ...     timeout=120,
            ...     retry_attempts=5
            ... )
        """
        config = ArkForgeConfig(api_key=api_key, base_url=base_url, **kwargs)
        super().__init__(config)

    def optimize_portfolio(self, request: OptimizePortfolioRequest) -> PortfolioRecommendation:
        """Optimize portfolio allocation.

        This method sends a portfolio optimization request to the ArkForge API
        and returns a recommendation with optimal asset allocation.

        Args:
            request: Portfolio optimization request

        Returns:
            Portfolio recommendation with allocation and metrics

        Raises:
            ValidationError: Invalid request parameters
            RateLimitError: Rate limit exceeded
            ServiceError: Server error
            NetworkError: Network communication error

        Example:
            >>> from arkforge.models import OptimizePortfolioRequest
            >>> request = OptimizePortfolioRequest(
            ...     assets=["BTC", "ETH", "SOL"],
            ...     risk_profile="moderate",
            ...     horizon_days=30
            ... )
            >>> result = client.optimize_portfolio(request)
            >>> print(f"Expected Return: {result.expected_return * 100:.2f}%")
            >>> print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        """
        response = self._http.request(
            method="POST",
            path="/api/v1/portfolio/optimize",
            json=request.model_dump(exclude_none=True, by_alias=True),
        )
        # Extract data.recommendation from response wrapper
        data = response.get("data", {}).get("recommendation", response)
        return PortfolioRecommendation.model_validate(data)

    async def optimize_portfolio_async(
        self, request: OptimizePortfolioRequest
    ) -> PortfolioRecommendation:
        """Optimize portfolio allocation (async).

        Asynchronous version of optimize_portfolio() for use in async contexts.

        Args:
            request: Portfolio optimization request

        Returns:
            Portfolio recommendation with allocation and metrics

        Raises:
            ValidationError: Invalid request parameters
            RateLimitError: Rate limit exceeded
            ServiceError: Server error
            NetworkError: Network communication error

        Example:
            >>> import asyncio
            >>> async def main():
            ...     result = await client.optimize_portfolio_async(request)
            ...     print(result.allocation)
            >>> asyncio.run(main())
        """
        response = await self._http.request_async(
            method="POST",
            path="/api/v1/portfolio/optimize",
            json=request.model_dump(exclude_none=True, by_alias=True),
        )
        # Extract data.recommendation from response wrapper
        data = response.get("data", {}).get("recommendation", response)
        return PortfolioRecommendation.model_validate(data)

    def get_risk_profiles(self) -> List[RiskProfile]:
        """Get available risk profiles.

        Returns a list of risk profiles with their descriptions and
        characteristics.

        Returns:
            List of risk profile descriptions

        Raises:
            RateLimitError: Rate limit exceeded
            ServiceError: Server error
            NetworkError: Network communication error

        Example:
            >>> profiles = client.get_risk_profiles()
            >>> for profile in profiles:
            ...     print(f"{profile.name}:")
            ...     print(f"  {profile.description}")
            ...     print(f"  Target Volatility: {profile.target_volatility}")
        """
        response = self._http.request(method="GET", path="/api/v1/portfolio/risk-profiles")
        return [RiskProfile.model_validate(rp) for rp in response]

    async def get_risk_profiles_async(self) -> List[RiskProfile]:
        """Get available risk profiles (async).

        Asynchronous version of get_risk_profiles().

        Returns:
            List of risk profile descriptions

        Example:
            >>> profiles = await client.get_risk_profiles_async()
        """
        response = await self._http.request_async(
            method="GET", path="/api/v1/portfolio/risk-profiles"
        )
        return [RiskProfile.model_validate(rp) for rp in response]

    def health(self) -> HealthStatus:
        """Check service health.

        Returns the health status of the ArkForge service and its dependencies.

        Returns:
            Health status with service availability

        Raises:
            NetworkError: Network communication error

        Example:
            >>> status = client.health()
            >>> print(f"Status: {status.status}")
            >>> print(f"Uptime: {status.uptime}s")
            >>> for service, state in status.services.items():
            ...     print(f"  {service}: {state}")
        """
        response = self._http.request(method="GET", path="/health")
        return HealthStatus.model_validate(response)

    async def health_async(self) -> HealthStatus:
        """Check service health (async).

        Asynchronous version of health().

        Returns:
            Health status with service availability

        Example:
            >>> status = await client.health_async()
        """
        response = await self._http.request_async(method="GET", path="/health")
        return HealthStatus.model_validate(response)
