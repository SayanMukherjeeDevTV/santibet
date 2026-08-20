"""Builds the composite `User`/`UserMe` view the frontend expects. Balance
comes live from the ledger; portfolio value / P&L / rank come from the
periodically-refreshed leaderboard_snapshot (see leaderboard_service) so
this stays cheap to call on every authenticated request.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import LeaderboardSnapshot
from app.models.user import User
from app.schemas.user import UserMe
from app.services import wallet_service


async def build_user_me(session: AsyncSession, user: User) -> UserMe:
    account = await wallet_service.get_or_create_user_account(session, user.id)
    balance = await wallet_service.get_balance(session, account.id)

    snapshot = await session.get(LeaderboardSnapshot, user.id)
    portfolio_value = Decimal(str(snapshot.portfolio_value)) if snapshot else balance
    total_pnl = Decimal(str(snapshot.total_pnl)) if snapshot else Decimal("0")
    total_pnl_percent = Decimal(str(snapshot.total_pnl_percent)) if snapshot else Decimal("0")
    rank = snapshot.rank if snapshot else 0

    return UserMe(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url or "",
        balance=float(balance),
        portfolio_value=float(portfolio_value),
        total_pnl=float(total_pnl),
        total_pnl_percent=float(total_pnl_percent),
        rank=rank,
        joined_at=user.created_at,
        verified=user.is_verified,
        role=user.role,
        kyc_status=user.kyc_status,
        account_status=user.account_status,
        is_real_money_eligible=user.is_real_money_eligible,
        region_code=user.region_code,
    )
