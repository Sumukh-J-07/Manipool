from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.ride_request import RideRequest
from backend.app.models.user import User
from backend.app.schemas.ride_request import MatchCandidateResponse
from backend.app.services.auth_service import get_current_user
from backend.app.services.matching_service import find_matches_for_request

router = APIRouter(prefix="/matching", tags=["Matching Algorithm"])


@router.get("/{request_id}", response_model=List[MatchCandidateResponse])
async def get_matches(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RideRequest).where(RideRequest.id == request_id)
    res = await db.execute(stmt)
    req = res.scalars().first()

    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride request not found.",
        )

    if req.user_id != current_user.id and current_user.role not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to query matches for this request.",
        )

    candidates = await find_matches_for_request(req, db)
    return candidates
