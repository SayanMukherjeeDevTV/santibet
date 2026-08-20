"""Recomputes the leaderboard_snapshot table from ledger balances, open
positions, and trade history. GET /leaderboard reads the snapshot directly
(cheap), so all the aggregation cost is paid here instead of on the request
path.

Implementation favors clarity over raw SQL cleverness - it does one query
per aggregate and combines them in Python. For very large user bases this
would be worth converting into a single SQL query or a materialized view
refreshed on the same schedule; the interface (rewrite leaderboard_snapshot)
would stay the same.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import LeaderboardSnapshot
from app.models.market import PriceHistory
from app.models.position import POSITION_LOST, POSITION_OPEN, POSITION_WON, Position
from app.models.trading import Trade
from app.models.user import User
from app.models.wallet import Account, DIRECTION_CREDIT, LedgerEntry, OWNER_USER


async def _latest_prices(session: AsyncSession) -> dict:
    """outcome_id -> latest price, via a correlated max(ts) subquery."""
    latest_ts_subq = (
        select(PriceHistory.outcome_id, func.max(PriceHistory.ts).label("max_ts"))
        .group_by(PriceHistory.outcome_id)
        .subquery()
    )
    stmt = select(PriceHistory.outcome_id, PriceHistory.price).join(
        latest_ts_subq,
        (PriceHistory.outcome_id == latest_ts_subq.c.outcome_id) & (PriceHistory.ts == latest_ts_subq.c.max_ts),
    )
    result = await session.execute(stmt)
    return {row.outcome_id: Decimal(str(row.price)) for row in result.all()}


async def _user_balances(session: AsyncSession) -> dict:
    stmt = (
        select(Account.owner_id, LedgerEntry.direction, func.sum(LedgerEntry.amount))
        .join(LedgerEntry, LedgerEntry.account_id == Account.id)
        .where(Account.owner_type == OWNER_USER)
        .group_by(Account.owner_id, LedgerEntry.direction)
    )
    result = await session.execute(stmt)
    balances: dict = {}
    for user_id, direction, total in result.all():
        total = Decimal(str(total))
        balances.setdefault(user_id, Decimal("0"))
        balances[user_id] += total if direction == DIRECTION_CREDIT else -total
    return balances


async def _user_volumes(session: AsyncSession) -> dict:
    buy_stmt = select(Trade.buyer_user_id, func.sum(Trade.price * Trade.shares)).group_by(Trade.buyer_user_id)
    sell_stmt = (
        select(Trade.seller_user_id, func.sum(Trade.price * Trade.shares))
        .where(Trade.seller_user_id.is_not(None))
        .group_by(Trade.seller_user_id)
    )
    volumes: dict = {}
    for user_id, total in (await session.execute(buy_stmt)).all():
        volumes[user_id] = volumes.get(user_id, Decimal("0")) + Decimal(str(total or 0))
    for user_id, total in (await session.execute(sell_stmt)).all():
        volumes[user_id] = volumes.get(user_id, Decimal("0")) + Decimal(str(total or 0))
    return volumes


async def refresh_leaderboard(session: AsyncSession) -> int:
    users = (await session.execute(select(User.id))).scalars().all()
    balances = await _user_balances(session)
    volumes = await _user_volumes(session)
    prices = await _latest_prices(session)

    all_positions = (await session.execute(select(Position))).scalars().all()

    per_user_positions: dict = {}
    for p in all_positions:
        per_user_positions.setdefault(p.user_id, []).append(p)

    now = datetime.now(timezone.utc)
    rows: list[tuple[Decimal, LeaderboardSnapshot]] = []

    for user_id in users:
        balance = balances.get(user_id, Decimal("0"))
        positions = per_user_positions.get(user_id, [])

        unrealized_value = Decimal("0")
        won = 0
        lost = 0
        markets_traded: set = set()

        for p in positions:
            markets_traded.add(p.market_id)
            if p.status == POSITION_OPEN:
                current_price = prices.get(p.outcome_id, Decimal(str(p.avg_price)))
                unrealized_value += Decimal(str(p.shares)) * current_price
            elif p.status == POSITION_WON:
                won += 1
            elif p.status == POSITION_LOST:
                lost += 1

        portfolio_value = balance + unrealized_value

        # Trading P&L: unrealized gain/loss on open positions, plus realized
        # gain/loss on closed (won/lost) positions. This is the standard
        # "how much have your trades made or lost you" figure, independent
        # of deposits/withdrawals.
        open_unrealized_pnl = sum(
            (
                Decimal(str(p.shares)) * prices.get(p.outcome_id, Decimal(str(p.avg_price)))
                - Decimal(str(p.invested))
                for p in positions
                if p.status == POSITION_OPEN
            ),
            Decimal("0"),
        )
        won_realized_pnl = sum(
            (
                Decimal(str(p.shares)) * Decimal("1.0000") - Decimal(str(p.invested))
                for p in positions
                if p.status == POSITION_WON
            ),
            Decimal("0"),
        )
        lost_realized_pnl = sum(
            (-Decimal(str(p.invested)) for p in positions if p.status == POSITION_LOST), Decimal("0")
        )
        total_pnl = open_unrealized_pnl + won_realized_pnl + lost_realized_pnl

        total_invested = sum((Decimal(str(p.invested)) for p in positions), Decimal("0"))
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else Decimal("0")

        closed = won + lost
        win_rate = Decimal(won) / Decimal(closed) if closed > 0 else Decimal("0")

        rows.append(
            (
                portfolio_value,
                LeaderboardSnapshot(
                    user_id=user_id,
                    rank=0,
                    portfolio_value=portfolio_value,
                    total_pnl=total_pnl,
                    total_pnl_percent=total_pnl_percent,
                    volume=volumes.get(user_id, Decimal("0")),
                    markets_traded=len(markets_traded),
                    win_rate=win_rate,
                    updated_at=now,
                ),
            )
        )

    rows.sort(key=lambda r: r[0], reverse=True)
    for i, (_, snapshot) in enumerate(rows, start=1):
        snapshot.rank = i

    await session.execute(delete(LeaderboardSnapshot))
    for _, snapshot in rows:
        session.add(snapshot)
    await session.flush()

    return len(rows)
