from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models.group import CarpoolGroup
from backend.app.models.group_member import GroupMember
from backend.app.models.ride_request import RideRequest
from backend.app.models.user import User
from backend.app.schemas.group import (
    BookRideRequest,
    CreateGroupRequest,
    DelayDepartureRequest,
    GroupDetailResponse,
    GroupMemberDetail,
    LeaveGroupRequest,
    UpdatePickupModeRequest,
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.chat_service import save_chat_message
from backend.app.services.concurrency_manager import group_transaction_lock
from backend.app.services.fare_service import VEHICLE_OPTIONS, split_fare
from backend.app.services.notification_service import (
    create_notification,
    notify_group_members,
)

router = APIRouter(prefix="/groups", tags=["Carpool Groups"])


async def _build_group_detail(group: CarpoolGroup, db: AsyncSession) -> GroupDetailResponse:
    stmt = (
        select(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group.id)
        .order_by(GroupMember.joined_at.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    member_details: List[GroupMemberDetail] = []
    for member, user in rows:
        member_details.append(
            GroupMemberDetail(
                id=member.id,
                user_id=user.id,
                name=user.name,
                email=user.email,
                area=user.area,
                acceptance_status=member.acceptance_status,
                membership_status=member.membership_status,
                fare_share_paise=member.fare_share_paise,
                joined_at=member.joined_at,
                accepted_at=member.accepted_at,
            )
        )

    return GroupDetailResponse(
        id=group.id,
        status=group.status,
        pickup_mode=group.pickup_mode,
        meeting_point_id=group.meeting_point_id,
        meeting_point_name=group.meeting_point_name,
        departure_time=group.departure_time,
        destination_id=group.destination_id,
        destination_name=group.destination_name,
        vehicle_type=group.vehicle_type,
        vehicle_capacity=group.vehicle_capacity,
        total_fare_paise=group.total_fare_paise,
        booked_by_user_id=group.booked_by_user_id,
        confirmed_at=group.confirmed_at,
        started_at=group.started_at,
        completed_at=group.completed_at,
        cancelled_at=group.cancelled_at,
        members=member_details,
        created_at=group.created_at,
    )


@router.post("", response_model=GroupDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    req: CreateGroupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Find active request of the creator
    stmt = select(RideRequest).where(
        RideRequest.user_id == current_user.id,
        RideRequest.status.in_(["SEARCHING", "MATCH_FOUND", "WAITING_FOR_ACCEPTANCE"]),
    )
    res = await db.execute(stmt)
    creator_req = res.scalars().first()
    if not creator_req:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must have an active ride request to form a carpool group.",
        )

    # Collect candidate requests
    candidate_stmt = select(RideRequest).where(
        RideRequest.id.in_(req.candidate_request_ids)
    )
    cand_res = await db.execute(candidate_stmt)
    candidate_reqs = cand_res.scalars().all()

    if not candidate_reqs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid candidate ride requests specified.",
        )

    v_config = VEHICLE_OPTIONS.get(req.vehicle_type, VEHICLE_OPTIONS["cab"])
    total_intended = 1 + len(candidate_reqs)
    if total_intended > v_config["capacity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proposed group of {total_intended} riders exceeds vehicle capacity of {v_config['capacity']} for {v_config['name']}.",
        )

    # Create Group
    group = CarpoolGroup(
        status="WAITING_FOR_ACCEPTANCE",
        pickup_mode=req.pickup_mode,
        meeting_point_id=creator_req.pickup_id,
        meeting_point_name=creator_req.pickup_name,
        departure_time=creator_req.departure,
        destination_id=creator_req.destination_id,
        destination_name=creator_req.destination_name,
        vehicle_type=req.vehicle_type,
        vehicle_capacity=v_config["capacity"],
        total_fare_paise=v_config["fare_paise"],
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)

    # Creator member (automatically accepted)
    creator_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        request_id=creator_req.id,
        acceptance_status="ACCEPTED",
        membership_status="ACTIVE",
        accepted_at=datetime.utcnow(),
    )
    db.add(creator_member)
    creator_req.group_id = group.id
    creator_req.status = "WAITING_FOR_ACCEPTANCE"

    # Add candidate members (pending acceptance)
    for c_req in candidate_reqs:
        if c_req.user_id == current_user.id:
            continue
        member = GroupMember(
            group_id=group.id,
            user_id=c_req.user_id,
            request_id=c_req.id,
            acceptance_status="PENDING",
            membership_status="ACTIVE",
        )
        db.add(member)
        c_req.group_id = group.id
        c_req.status = "WAITING_FOR_ACCEPTANCE"

        # Send notification to invited student
        await create_notification(
            db=db,
            user_id=c_req.user_id,
            title="Carpool Group Match!",
            message=f"{current_user.name} invited you to join a shared carpool to {creator_req.destination_name}.",
            event_type="MATCH_FOUND",
            payload={"group_id": group.id},
        )

    await db.commit()

    # Create initial system chat message
    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text=f"Carpool proposed by {current_user.name}. Waiting for all riders to accept.",
        is_system=True,
    )

    return await _build_group_detail(group, db)


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group_detail(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    # Access control: user must be member or reviewer
    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group.id,
        GroupMember.user_id == current_user.id,
    )
    mem_res = await db.execute(mem_stmt)
    is_member = mem_res.scalars().first()

    if not is_member and current_user.role not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this private group's information.",
        )

    return await _build_group_detail(group, db)


@router.post("/{group_id}/accept", response_model=GroupDetailResponse)
async def accept_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Lock this specific group during acceptance to prevent concurrency race conditions
    async with group_transaction_lock(group_id):
        stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
        res = await db.execute(stmt)
        group = res.scalars().first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carpool group not found.",
            )

        if group.status in ("COMPLETED", "CANCELLED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot accept group in status {group.status}.",
            )

        # Get existing members
        mem_stmt = select(GroupMember).where(GroupMember.group_id == group_id)
        mem_res = await db.execute(mem_stmt)
        all_members = mem_res.scalars().all()

        active_accepted = [
            m for m in all_members if m.membership_status == "ACTIVE" and m.acceptance_status == "ACCEPTED"
        ]

        target_member = next((m for m in all_members if m.user_id == current_user.id), None)
        if not target_member:
            # Check capacity before adding new member
            if len(active_accepted) >= group.vehicle_capacity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Group is already at maximum capacity ({group.vehicle_capacity} seats).",
                )
            target_member = GroupMember(
                group_id=group.id,
                user_id=current_user.id,
                acceptance_status="ACCEPTED",
                membership_status="ACTIVE",
                accepted_at=datetime.utcnow(),
            )
            db.add(target_member)
        else:
            if target_member.acceptance_status == "ACCEPTED":
                # Idempotent: already accepted
                return await _build_group_detail(group, db)

            if len(active_accepted) >= group.vehicle_capacity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Group is already at maximum capacity ({group.vehicle_capacity} seats).",
                )

            target_member.acceptance_status = "ACCEPTED"
            target_member.membership_status = "ACTIVE"
            target_member.accepted_at = datetime.utcnow()

        # Update user's ride request if linked
        req_stmt = select(RideRequest).where(
            RideRequest.user_id == current_user.id,
            RideRequest.status.in_(["SEARCHING", "MATCH_FOUND", "WAITING_FOR_ACCEPTANCE"]),
        )
        req_res = await db.execute(req_stmt)
        user_req = req_res.scalars().first()
        if user_req:
            user_req.group_id = group.id
            user_req.status = "WAITING_FOR_ACCEPTANCE"
            target_member.request_id = user_req.id

        await db.commit()

        # Check if ALL active members in the group are now accepted
        mem_res2 = await db.execute(mem_stmt)
        updated_members = mem_res2.scalars().all()
        all_active = [m for m in updated_members if m.membership_status == "ACTIVE"]
        all_accepted = all(m.acceptance_status == "ACCEPTED" for m in all_active)

        if all_accepted and len(all_active) >= 2:
            group.status = "GROUP_FORMED"
            for m in all_active:
                if m.request_id:
                    r_stmt = select(RideRequest).where(RideRequest.id == m.request_id)
                    r_res = await db.execute(r_stmt)
                    r = r_res.scalars().first()
                    if r:
                        r.status = "GROUP_FORMED"

            await db.commit()

            # Broadcast system message and notifications
            await save_chat_message(
                db=db,
                group_id=group.id,
                sender_id="system",
                sender_name="Carpool",
                text="All riders accepted! Group formed. You can now chat and coordinate pickup.",
                is_system=True,
            )
            await notify_group_members(
                db=db,
                group_id=group.id,
                title="Carpool Group Formed!",
                message="All riders accepted. Check chat to coordinate pickup.",
                event_type="GROUP_FORMED",
            )
        else:
            await save_chat_message(
                db=db,
                group_id=group.id,
                sender_id="system",
                sender_name="Carpool",
                text=f"{current_user.name} accepted the carpool.",
                is_system=True,
            )

        return await _build_group_detail(group, db)


@router.post("/{group_id}/decline")
async def decline_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
    )
    mem_res = await db.execute(mem_stmt)
    member = mem_res.scalars().first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this group.",
        )

    member.acceptance_status = "DECLINED"
    member.membership_status = "LEFT"
    member.left_at = datetime.utcnow()

    # Reset ride request to searching
    if member.request_id:
        req_stmt = select(RideRequest).where(RideRequest.id == member.request_id)
        req_res = await db.execute(req_stmt)
        r = req_res.scalars().first()
        if r:
            r.group_id = None
            r.status = "SEARCHING"

    await db.commit()

    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text=f"{current_user.name} declined the invitation.",
        is_system=True,
    )

    return {"message": "Invitation declined.", "group_id": group_id}


@router.post("/{group_id}/pickup-mode", response_model=GroupDetailResponse)
async def update_pickup_mode(
    group_id: str,
    req: UpdatePickupModeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    if req.mode not in ("common", "sequential"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pickup mode must be 'common' or 'sequential'.",
        )

    group.pickup_mode = req.mode
    if req.meeting_point_id:
        group.meeting_point_id = req.meeting_point_id
    if req.meeting_point_name:
        group.meeting_point_name = req.meeting_point_name

    await db.commit()

    mode_label = "Common Meeting Point" if req.mode == "common" else "Sequential Pickup"
    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text=f"{current_user.name} changed pickup arrangement to {mode_label}.",
        is_system=True,
    )

    await notify_group_members(
        db=db,
        group_id=group.id,
        title="Pickup Arrangement Updated",
        message=f"Pickup changed to {mode_label} by {current_user.name}.",
        event_type="PICKUP_UPDATED",
        exclude_user_id=current_user.id,
    )

    return await _build_group_detail(group, db)


@router.post("/{group_id}/delay", response_model=GroupDetailResponse)
async def delay_departure(
    group_id: str,
    req: DelayDepartureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    group.departure_time = group.departure_time + timedelta(minutes=req.minutes)
    await db.commit()

    time_str = group.departure_time.strftime("%H:%M")
    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text=f"{current_user.name} adjusted departure +{req.minutes} mins (New: {time_str}).",
        is_system=True,
    )

    await notify_group_members(
        db=db,
        group_id=group.id,
        title="Departure Adjusted",
        message=f"Departure postponed by {req.minutes} mins to {time_str}.",
        event_type="DEPARTURE_UPDATED",
        exclude_user_id=current_user.id,
    )

    return await _build_group_detail(group, db)


@router.post("/{group_id}/book", response_model=GroupDetailResponse)
async def book_ride(
    group_id: str,
    req: BookRideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    # Get active accepted members
    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.membership_status == "ACTIVE",
        GroupMember.acceptance_status == "ACCEPTED",
    )
    mem_res = await db.execute(mem_stmt)
    active_members = mem_res.scalars().all()
    num_riders = len(active_members)

    if num_riders < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a carpool without active accepted members.",
        )

    v_config = VEHICLE_OPTIONS.get(req.vehicle_type)
    if not v_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vehicle type. Supported: 'cab', 'auto'.",
        )

    # Enforce vehicle capacity
    if num_riders > v_config["capacity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{v_config['name']} capacity is {v_config['capacity']} riders, but group has {num_riders} active riders.",
        )

    total_fare = req.fare_paise or v_config["fare_paise"]
    shares = split_fare(total_fare, num_riders)

    for idx, member in enumerate(active_members):
        member.fare_share_paise = shares[idx]

    group.vehicle_type = req.vehicle_type
    group.vehicle_capacity = v_config["capacity"]
    group.total_fare_paise = total_fare
    group.booked_by_user_id = current_user.id
    group.confirmed_at = datetime.utcnow()
    group.status = "RIDE_BOOKED"

    # Update ride requests
    for m in active_members:
        if m.request_id:
            r_stmt = select(RideRequest).where(RideRequest.id == m.request_id)
            r_res = await db.execute(r_stmt)
            r = r_res.scalars().first()
            if r:
                r.status = "RIDE_BOOKED"

    await db.commit()

    fare_str = f"₹{total_fare / 100:.2f}"
    per_person = f"₹{shares[0] / 100:.2f}"
    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text=f"Ride booked by {current_user.name} ({v_config['name']}). Total: {fare_str} (~{per_person}/rider).",
        is_system=True,
    )

    await notify_group_members(
        db=db,
        group_id=group.id,
        title="Ride Booked!",
        message=f"{current_user.name} booked the {v_config['name']}. Fare: {fare_str}.",
        event_type="RIDE_BOOKED",
        exclude_user_id=current_user.id,
    )

    return await _build_group_detail(group, db)


@router.post("/{group_id}/start", response_model=GroupDetailResponse)
async def start_ride(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    if group.status != "RIDE_BOOKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start ride from status {group.status}. Booking must be confirmed first.",
        )

    group.status = "IN_PROGRESS"
    group.started_at = datetime.utcnow()

    # Update ride requests
    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id, GroupMember.membership_status == "ACTIVE"
    )
    mem_res = await db.execute(mem_stmt)
    for m in mem_res.scalars().all():
        if m.request_id:
            r_stmt = select(RideRequest).where(RideRequest.id == m.request_id)
            r_res = await db.execute(r_stmt)
            r = r_res.scalars().first()
            if r:
                r.status = "IN_PROGRESS"

    await db.commit()

    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text="Journey started! Have a safe ride.",
        is_system=True,
    )

    return await _build_group_detail(group, db)


@router.post("/{group_id}/complete", response_model=GroupDetailResponse)
async def complete_ride(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    if group.status not in ("RIDE_BOOKED", "IN_PROGRESS"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete ride from status {group.status}.",
        )

    group.status = "COMPLETED"
    group.completed_at = datetime.utcnow()

    # Update ride requests to COMPLETED
    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id, GroupMember.membership_status == "ACTIVE"
    )
    mem_res = await db.execute(mem_stmt)
    for m in mem_res.scalars().all():
        if m.request_id:
            r_stmt = select(RideRequest).where(RideRequest.id == m.request_id)
            r_res = await db.execute(r_stmt)
            r = r_res.scalars().first()
            if r:
                r.status = "COMPLETED"

    await db.commit()

    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text="Journey completed! Thank you for carpooling with ManiPool.",
        is_system=True,
    )

    await notify_group_members(
        db=db,
        group_id=group.id,
        title="Journey Completed",
        message="Your carpool journey has finished.",
        event_type="RIDE_COMPLETED",
    )

    return await _build_group_detail(group, db)


@router.post("/{group_id}/leave")
async def leave_group(
    group_id: str,
    body: Optional[LeaveGroupRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CarpoolGroup).where(CarpoolGroup.id == group_id)
    res = await db.execute(stmt)
    group = res.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carpool group not found.",
        )

    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.membership_status == "ACTIVE",
    )
    mem_res = await db.execute(mem_stmt)
    member = mem_res.scalars().first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not an active member of this group.",
        )

    # Mark member as left
    member.membership_status = "LEFT"
    member.left_at = datetime.utcnow()

    # Cancel user's request
    if member.request_id:
        r_stmt = select(RideRequest).where(RideRequest.id == member.request_id)
        r_res = await db.execute(r_stmt)
        r = r_res.scalars().first()
        if r:
            r.status = "CANCELLED"

    await db.flush()

    # Check remaining active members
    remaining_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.id != member.id,
        GroupMember.membership_status == "ACTIVE",
        GroupMember.acceptance_status == "ACCEPTED",
    )
    rem_res = await db.execute(remaining_stmt)
    remaining_members = rem_res.scalars().all()

    if len(remaining_members) == 0:
        group.status = "CANCELLED"
        group.cancelled_at = datetime.utcnow()
        group.cancellation_reason = body.reason if body else "All members left"
    else:
        # Recalculate fare for remaining members if ride was booked
        if group.status == "RIDE_BOOKED":
            new_shares = split_fare(group.total_fare_paise, len(remaining_members))
            for idx, rem in enumerate(remaining_members):
                rem.fare_share_paise = new_shares[idx]

    await db.commit()

    await save_chat_message(
        db=db,
        group_id=group.id,
        sender_id="system",
        sender_name="Carpool",
        text=f"{current_user.name} left the group.",
        is_system=True,
    )

    await notify_group_members(
        db=db,
        group_id=group.id,
        title="Member Left Carpool",
        message=f"{current_user.name} has left the carpool group.",
        event_type="MEMBER_LEFT",
    )

    return {
        "message": "Successfully left the group.",
        "group_id": group_id,
        "remaining_members_count": len(remaining_members),
    }
