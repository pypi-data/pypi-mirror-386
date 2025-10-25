"""Base client implementation with shared functionality."""

from typing import Any

from ._http import HTTPClient
from .config import ArkForgeConfig


class BaseClient:
    """Base client with shared functionality.

    This class provides common functionality for all client classes,
    including HTTP client management and lifecycle methods.

    Attributes:
        config: ArkForge configuration
    """

    def __init__(self, config: ArkForgeConfig):
        """Initialize base client.

        Args:
            config: ArkForge configuration
        """
        self.config = config
        self._http = HTTPClient(config)

    def __enter__(self) -> "BaseClient":
        """Context manager entry.

        Example:
            >>> with ArkForgeClient(api_key="...") as client:
            ...     result = client.optimize_portfolio(request)
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close HTTP clients and clean up resources.

        This should be called when done with the client.
        """
        self._http.close()
