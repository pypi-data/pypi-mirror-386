"""Common data models and enums for ArkForge SDK."""

from enum import Enum


class RiskProfileType(str, Enum):
    """Risk profile types for portfolio optimization.

    Attributes:
        CONSERVATIVE: Low-risk, stable returns
        MODERATE: Balanced risk and return
        AGGRESSIVE: High-risk, high potential returns
    """

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ActionType(str, Enum):
    """Portfolio action types.

    Attributes:
        BUY: Increase position in asset
        SELL: Decrease position in asset
        HOLD: Maintain current position
    """

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OptimizationGoal(str, Enum):
    """Portfolio optimization goals.

    Attributes:
        SHARPE: Maximize Sharpe ratio (risk-adjusted returns)
        RETURN: Maximize expected returns
        RISK: Minimize risk/volatility
    """

    SHARPE = "sharpe"
    RETURN = "return"
    RISK = "risk"


class LLMProvider(str, Enum):
    """LLM provider types.

    Attributes:
        OPENAI: OpenAI (GPT-4, etc.)
        ANTHROPIC: Anthropic (Claude)
        XAI: xAI (Grok)
        MISTRAL: Mistral AI
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"
    MISTRAL = "mistral"


class HealthStatusType(str, Enum):
    """Service health status types.

    Attributes:
        OK: All services operational
        DEGRADED: Some services degraded
        DOWN: Service unavailable
    """

    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"
