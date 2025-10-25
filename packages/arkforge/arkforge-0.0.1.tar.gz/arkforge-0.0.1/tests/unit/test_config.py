"""Unit tests for configuration."""

import os
import pytest
from arkforge.config import ArkForgeConfig


def test_config_creation():
    """Test basic config creation."""
    config = ArkForgeConfig(api_key="sk-arkforge-test-key")
    assert config.api_key == "sk-arkforge-test-key"
    assert config.base_url == "http://localhost:3001"
    assert config.timeout == 60


def test_config_custom_values():
    """Test config with custom values."""
    config = ArkForgeConfig(
        api_key="sk-arkforge-test-key",
        base_url="https://api.arkforge.io",
        timeout=120,
        retry_attempts=5,
    )
    assert config.base_url == "https://api.arkforge.io"
    assert config.timeout == 120
    assert config.retry_attempts == 5


def test_config_api_key_validation():
    """Test API key validation."""
    with pytest.raises(ValueError, match="api_key is required"):
        ArkForgeConfig(api_key="")


def test_config_from_env(monkeypatch):
    """Test loading config from environment."""
    monkeypatch.setenv("ARKFORGE_API_KEY", "sk-arkforge-env-key")
    config = ArkForgeConfig.from_env()
    assert config.api_key == "sk-arkforge-env-key"


def test_config_from_env_missing_key():
    """Test from_env with missing API key."""
    # Clear env var if it exists
    if "ARKFORGE_API_KEY" in os.environ:
        old_key = os.environ.pop("ARKFORGE_API_KEY")
    else:
        old_key = None

    try:
        with pytest.raises(ValueError, match="ARKFORGE_API_KEY environment variable not set"):
            ArkForgeConfig.from_env()
    finally:
        # Restore env var if it existed
        if old_key:
            os.environ["ARKFORGE_API_KEY"] = old_key


def test_user_agent_generation():
    """Test user agent is generated."""
    config = ArkForgeConfig(api_key="sk-arkforge-test-key")
    assert config.user_agent is not None
    assert "arkforge-python" in config.user_agent
