# Changelog

All notable changes to the ArkForge Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-23

### Added
- Initial release of ArkForge Python SDK
- `ArkForgeClient` for portfolio optimization operations
- `KeyManagementClient` for API key lifecycle management
- Pydantic v2 models for type-safe request/response handling
- Automatic retry with exponential backoff
- Client-side rate limiting with token bucket algorithm
- Comprehensive error hierarchy with retryable/non-retryable classification
- Synchronous and asynchronous API support
- Full type hints for excellent IDE support
- API key validation and secure credential management
- Environment variable configuration support
- Context manager support for automatic resource cleanup

### Portfolio Optimization Features
- Optimize portfolio allocation based on risk profile
- Support for custom constraints (max position size, diversification)
- Advanced optimization goals (Sharpe ratio, returns, risk)
- Forecast and sentiment analysis integration
- Rebalancing recommendations with swap instructions

### API Key Management Features
- Create, list, and revoke API keys
- Key rotation for security
- Scope management
- Usage statistics and monitoring

[0.1.0]: https://github.com/yourusername/arkforge-sdk-py/releases/tag/v0.1.0
