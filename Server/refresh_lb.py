import asyncio
from app.db.session import AsyncSessionLocal
from app.services.leaderboard_service import refresh_leaderboard

async def main():
    async with AsyncSessionLocal() as session:
        count = await refresh_leaderboard(session)
        await session.commit()
        print(f"Refreshed leaderboard for {count} users")

asyncio.run(main())
