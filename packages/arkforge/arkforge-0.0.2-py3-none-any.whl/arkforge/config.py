"""Configuration management for ArkForge SDK."""

import dataclasses
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ArkForgeConfig:
    """ArkForge SDK configuration.

    This class manages all configuration options for the SDK, including
    API credentials, timeouts, retry behavior, and debugging.

    Attributes:
        api_key: ArkForge API key (required, starts with 'sk-arkforge-')
        base_url: API base URL (default: http://localhost:3001)
        timeout: Request timeout in seconds (default: 60)
        retry_attempts: Maximum retry attempts (default: 3)
        retry_delay: Base retry delay in seconds (default: 1.0)
        debug: Enable debug logging (default: False)
        user_agent: Custom user agent string (auto-generated if None)

    Example:
        >>> config = ArkForgeConfig(api_key="sk-arkforge-abc123")
        >>> config = ArkForgeConfig.from_env()  # Load from environment
    """

    api_key: str
    base_url: str = "http://localhost:3001"
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0
    debug: bool = False
    user_agent: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and initialize configuration."""
        # Validate API key is provided
        if not self.api_key:
            raise ValueError("api_key is required")

        # Validate API key format
        if not self.api_key.startswith("sk-arkforge-"):
            raise ValueError("Invalid API key format. " "API key must start with 'sk-arkforge-'")

        # Validate numeric parameters
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        if self.retry_attempts < 0:
            raise ValueError("retry_attempts must be non-negative")

        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")

        # Generate user agent if not provided
        if self.user_agent is None:
            from .version import __version__

            python_version = sys.version.split()[0]
            self.user_agent = f"arkforge-python/{__version__} python/{python_version}"

        # Store version for X-Client-Version header
        from .version import __version__

        self.version = __version__

    @classmethod
    def from_env(cls, **overrides: Any) -> "ArkForgeConfig":
        """Load configuration from environment variables.

        This method provides an easy way to load configuration from
        environment variables, which is the recommended approach for
        production deployments.

        Environment variables:
            ARKFORGE_API_KEY: API key (required)
            ARKFORGE_BASE_URL: Base URL (optional)

        Args:
            **overrides: Additional config overrides

        Returns:
            ArkForgeConfig instance

        Raises:
            ValueError: If ARKFORGE_API_KEY environment variable is not set

        Example:
            >>> import os
            >>> os.environ["ARKFORGE_API_KEY"] = "sk-arkforge-abc123"
            >>> config = ArkForgeConfig.from_env(timeout=120)
        """
        api_key = os.getenv("ARKFORGE_API_KEY")
        if not api_key:
            raise ValueError(
                "ARKFORGE_API_KEY environment variable not set. "
                "Please set it or pass api_key directly to ArkForgeClient."
            )

        # Get base URL from environment or use default
        default_field = cls.__dataclass_fields__["base_url"].default
        if isinstance(default_field, str):
            default_url = default_field
        elif default_field == dataclasses.MISSING:
            default_url = "http://localhost:3001"
        else:
            default_url = "http://localhost:3001"
        base_url_str: str = os.getenv("ARKFORGE_BASE_URL", default_url)

        return cls(api_key=api_key, base_url=base_url_str, **overrides)

    def __repr__(self) -> str:
        """Mask API key in repr for security."""
        # Show only first 16 characters of API key
        masked_key = f"{self.api_key[:16]}..." if len(self.api_key) > 16 else "***"

        return (
            f"ArkForgeConfig("
            f"api_key={masked_key}, "
            f"base_url={self.base_url!r}, "
            f"timeout={self.timeout}, "
            f"retry_attempts={self.retry_attempts}, "
            f"debug={self.debug})"
        )
