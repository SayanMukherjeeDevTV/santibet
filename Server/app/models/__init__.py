"""Import every model module here so that `Base.metadata` is fully populated
when Alembic's env.py imports this package for autogenerate support."""
from app.models.admin import AuditLog, LeaderboardSnapshot  # noqa: F401
from app.models.ai import AIMarketDraft, AIRecommendation, MarketSignal  # noqa: F401
from app.models.market import (  # noqa: F401
    Category,
    Market,
    MarketOutcome,
    MarketReport,
    MarketStats,
    PriceHistory,
)
from app.models.position import Position  # noqa: F401
from app.models.trading import AMMPool, Order, Trade  # noqa: F401
from app.models.user import (  # noqa: F401
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    User,
)
from app.models.wallet import Account, LedgerEntry, Payment  # noqa: F401

__all__ = [
    "AuditLog",
    "LeaderboardSnapshot",
    "AIMarketDraft",
    "AIRecommendation",
    "MarketSignal",
    "Category",
    "Market",
    "MarketOutcome",
    "MarketReport",
    "MarketStats",
    "PriceHistory",
    "Position",
    "AMMPool",
    "Order",
    "Trade",
    "EmailVerificationToken",
    "PasswordResetToken",
    "RefreshToken",
    "User",
    "Account",
    "LedgerEntry",
    "Payment",
]
