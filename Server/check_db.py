import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.user import User
from app.models.trading import Trade
from app.models.position import Position

async def main():
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User).where(User.name == 'Sayan Mukherjee'))).scalars().all()
        for u in users:
            print(f"User: {u.id} {u.name}")
            trades = (await session.execute(select(Trade).where((Trade.buyer_user_id == u.id) | (Trade.seller_user_id == u.id)))).scalars().all()
            print(f"Trades: {len(trades)}")
            positions = (await session.execute(select(Position).where(Position.user_id == u.id))).scalars().all()
            print(f"Positions: {len(positions)}")
            for t in trades:
                print(f"Trade: {t.id} {t.price} {t.shares} buyer={t.buyer_user_id} seller={t.seller_user_id}")
            for p in positions:
                print(f"Position: {p.id} {p.market_id} {p.shares} {p.status}")

asyncio.run(main())
