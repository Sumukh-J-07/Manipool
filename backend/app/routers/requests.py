from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.ride_request import RideRequest
from backend.app.models.user import User
from backend.app.schemas.ride_request import (
    RideRematchRequest,
    RideRequestCreate,
    RideRequestResponse,
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.matching_service import (
    LOCATIONS_COORDS,
    find_matches_for_request,
)

router = APIRouter(prefix="/requests", tags=["Ride Requests"])

OPEN_STATUSES = [
    "DRAFT",
    "SEARCHING",
    "MATCH_FOUND",
    "WAITING_FOR_ACCEPTANCE",
    "GROUP_FORMED",
    "RIDE_BOOKED",
    "IN_PROGRESS",
    "NO_MATCH",
    "REMATCHING",
]


@router.post("", response_model=RideRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_ride_request(
    req: RideRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate pickup and destination
    if req.pickup_id == req.destination_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pickup and destination must be different.",
        )

    pickup_loc = LOCATIONS_COORDS.get(req.pickup_id)
    dest_loc = LOCATIONS_COORDS.get(req.destination_id)
    if not pickup_loc or not dest_loc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pickup or destination landmark identifier.",
        )

    # Validate departure is in future
    now_utc = datetime.utcnow()
    # Normalize req.departure to naive UTC if needed
    departure_naive = req.departure.replace(tzinfo=None)
    if departure_naive <= now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose a departure in the future.",
        )

    if req.flexibility not in (0, 15, 30, 45):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flexibility must be 0, 15, 30, or 45 minutes.",
        )

    # Enforce: Only ONE open request per user at any time
    stmt = select(RideRequest).where(
        RideRequest.user_id == current_user.id,
        RideRequest.status.in_(OPEN_STATUSES),
    )
    res = await db.execute(stmt)
    active_req = res.scalars().first()
    if active_req:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have an active request ({active_req.id}) in status {active_req.status}. Complete or cancel it first.",
        )

    new_req = RideRequest(
        user_id=current_user.id,
        pickup_id=req.pickup_id,
        pickup_name=pickup_loc["name"],
        pickup_area=pickup_loc["area"],
        pickup_lat=pickup_loc.get("lat"),
        pickup_lng=pickup_loc.get("lng"),
        destination_id=req.destination_id,
        destination_name=dest_loc["name"],
        destination_area=dest_loc["area"],
        destination_corridor=dest_loc["corridor"],
        destination_lat=dest_loc.get("lat"),
        destination_lng=dest_loc.get("lng"),
        departure=departure_naive,
        flexibility=req.flexibility,
        status="SEARCHING",
    )
    db.add(new_req)
    await db.commit()
    await db.refresh(new_req)

    # Search for real matching candidates in DB
    matches = await find_matches_for_request(new_req, db)
    if matches:
        new_req.status = "MATCH_FOUND"
        await db.commit()
        await db.refresh(new_req)

    resp = RideRequestResponse.model_validate(new_req)
    resp.matches = matches
    return resp


@router.get("", response_model=List[RideRequestResponse])
async def list_user_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(RideRequest)
        .where(RideRequest.user_id == current_user.id)
        .order_by(RideRequest.created_at.desc())
    )
    res = await db.execute(stmt)
    requests = res.scalars().all()

    output: List[RideRequestResponse] = []
    for r in requests:
        matches = []
        if r.status in ("SEARCHING", "MATCH_FOUND"):
            matches = await find_matches_for_request(r, db)
        item = RideRequestResponse.model_validate(r)
        item.matches = matches
        output.append(item)

    return output


@router.get("/{request_id}", response_model=RideRequestResponse)
async def get_request_detail(
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

    # Access control: user must own the request or be a reviewer
    if req.user_id != current_user.id and current_user.role not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this private request.",
        )

    matches = []
    if req.status in ("SEARCHING", "MATCH_FOUND"):
        matches = await find_matches_for_request(req, db)

    resp = RideRequestResponse.model_validate(req)
    resp.matches = matches
    return resp


@router.delete("/{request_id}")
async def cancel_request(
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

    if req.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own ride requests.",
        )

    if req.status in ("COMPLETED", "CANCELLED", "EXPIRED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a request that is already {req.status}.",
        )

    req.status = "CANCELLED"
    await db.commit()
    return {"message": "Ride request cancelled successfully.", "request_id": request_id}


@router.post("/{request_id}/rematch", response_model=RideRequestResponse)
async def rematch_request(
    request_id: str,
    body: RideRematchRequest,
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

    if req.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to rematch this request.",
        )

    if body.flexibility is not None:
        if body.flexibility not in (0, 15, 30, 45):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supported flexibility values: 0, 15, 30, 45.",
            )
        req.flexibility = body.flexibility

    req.status = "REMATCHING"
    await db.commit()
    await db.refresh(req)

    matches = await find_matches_for_request(req, db)
    req.status = "MATCH_FOUND" if matches else "NO_MATCH"
    await db.commit()
    await db.refresh(req)

    resp = RideRequestResponse.model_validate(req)
    resp.matches = matches
    return resp
