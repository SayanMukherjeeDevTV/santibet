from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserMe, UserUpdateRequest
from app.services import user_view_service

router = APIRouter()


@router.get("/me", response_model=UserMe)
async def get_me(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await user_view_service.build_user_me(session, user)


@router.patch("/me", response_model=UserMe)
async def update_me(
    body: UserUpdateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name.strip()
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    if body.region_code is not None:
        user.region_code = body.region_code
    await session.flush()
    return await user_view_service.build_user_me(session, user)
