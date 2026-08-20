"""One-time (idempotent) seed data: the 7 market categories the frontend
expects (client/lib/types.ts `MarketCategory`), plus a dev admin user so the
admin panel is reachable immediately after setup.

Run with:  python -m scripts.seed
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.market import Category
from app.models.user import ROLE_ADMIN, User
from app.services import wallet_service

CATEGORIES = [
    {"id": "politics", "label": "Politics", "icon": "landmark", "color": "#ef4444", "description": "Elections, legislation, and government outcomes."},
    {"id": "crypto", "label": "Crypto", "icon": "bitcoin", "color": "#f59e0b", "description": "Cryptocurrency prices, protocol events, and adoption milestones."},
    {"id": "sports", "label": "Sports", "icon": "trophy", "color": "#22c55e", "description": "Match outcomes, championships, and season results."},
    {"id": "economy", "label": "Economy", "icon": "trending-up", "color": "#3b82f6", "description": "Interest rates, inflation, and macroeconomic indicators."},
    {"id": "entertainment", "label": "Entertainment", "icon": "film", "color": "#a855f7", "description": "Awards, box office, and pop culture events."},
    {"id": "technology", "label": "Technology", "icon": "cpu", "color": "#06b6d4", "description": "Product launches, tech company milestones, and industry events."},
    {"id": "world", "label": "World", "icon": "globe", "color": "#64748b", "description": "International affairs and global events."},
]

DEV_ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "admin@santibet.dev")
DEV_ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe123!")


async def seed_categories(session) -> int:
    created = 0
    for c in CATEGORIES:
        existing = await session.get(Category, c["id"])
        if existing is None:
            session.add(Category(**c))
            created += 1
    await session.flush()
    return created


async def seed_admin(session) -> bool:
    existing = (await session.execute(select(User).where(User.email == DEV_ADMIN_EMAIL))).scalar_one_or_none()
    if existing is not None:
        return False
    admin = User(
        email=DEV_ADMIN_EMAIL,
        password_hash=hash_password(DEV_ADMIN_PASSWORD),
        name="SantiBet Admin",
        role=ROLE_ADMIN,
        is_verified=True,
    )
    session.add(admin)
    await session.flush()
    await wallet_service.get_or_create_user_account(session, admin.id)
    return True


async def main() -> None:
    async with AsyncSessionLocal() as session:
        cats_created = await seed_categories(session)
        admin_created = await seed_admin(session)
        await session.commit()
        print(f"Seeded {cats_created} new categories.")
        if admin_created:
            print(f"Created dev admin user: {DEV_ADMIN_EMAIL} / {DEV_ADMIN_PASSWORD}  (CHANGE THIS PASSWORD)")
        else:
            print(f"Admin user {DEV_ADMIN_EMAIL} already exists - skipped.")


if __name__ == "__main__":
    asyncio.run(main())
