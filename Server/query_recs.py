import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.ai import AIRecommendation

async def main():
    async with async_session_maker() as session:
        result = await session.execute(select(AIRecommendation))
        recs = result.scalars().all()
        print(f"Total recommendations in DB: {len(recs)}")
        for rec in recs:
            print(f"ID: {rec.id}, Status: {rec.review_status}")

asyncio.run(main())
