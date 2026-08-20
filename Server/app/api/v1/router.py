from fastapi import APIRouter

from app.api.v1.routers import (
    admin,
    ai,
    auth,
    leaderboard,
    markets,
    positions,
    trading,
    users,
    wallet,
    webhooks,
    ws,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(markets.router, prefix="/markets", tags=["markets"])
api_router.include_router(markets.categories_router, prefix="/categories", tags=["markets"])
api_router.include_router(markets.stats_router, prefix="/platform-stats", tags=["markets"])
api_router.include_router(trading.router, tags=["trading"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(wallet.kyc_router, prefix="/kyc", tags=["kyc"])
api_router.include_router(positions.router, tags=["positions"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(ws.router, tags=["realtime"])
