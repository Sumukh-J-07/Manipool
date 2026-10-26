from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.report import IssueReport
from backend.app.models.user import User
from backend.app.schemas.report import (
    IssueReportCreate,
    IssueReportResponse,
    IssueReportReviewUpdate,
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.notification_service import create_notification

router = APIRouter(tags=["Issue Reports & Safety"])


@router.post("/reports", response_model=IssueReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    req: IssueReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = IssueReport(
        user_id=current_user.id,
        ride_id=req.ride_id,
        group_id=req.group_id,
        text=req.text.strip(),
        category=req.category.upper(),
        status="OPEN",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # In-app notification to student confirming receipt
    await create_notification(
        db=db,
        user_id=current_user.id,
        title="Report Received",
        message="Your report has been submitted to the MAHE Carpool review team. We will follow up shortly.",
        event_type="REPORT_RECEIVED",
        payload={"report_id": report.id},
    )

    return IssueReportResponse.model_validate(report)


@router.get("/reports", response_model=List[IssueReportResponse])
async def list_my_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(IssueReport)
        .where(IssueReport.user_id == current_user.id)
        .order_by(IssueReport.created_at.desc())
    )
    res = await db.execute(stmt)
    reports = res.scalars().all()
    return [IssueReportResponse.model_validate(r) for r in reports]


@router.get("/admin/reports", response_model=List[IssueReportResponse])
async def list_all_reports_for_reviewer(
    report_status: Optional[str] = Query(None, alias="status"),
    x_admin_key: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify reviewer permission either by user role or admin api key
    is_authorized = (
        (current_user and current_user.role in ("reviewer", "admin"))
        or (x_admin_key and x_admin_key == settings.ADMIN_API_KEY)
    )
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Designated reviewer access required to inspect reports.",
        )

    stmt = select(IssueReport).order_by(IssueReport.created_at.desc())
    if report_status:
        stmt = stmt.where(IssueReport.status == report_status.upper())

    res = await db.execute(stmt)
    reports = res.scalars().all()
    return [IssueReportResponse.model_validate(r) for r in reports]


@router.patch("/admin/reports/{report_id}", response_model=IssueReportResponse)
async def review_report(
    report_id: str,
    body: IssueReportReviewUpdate,
    x_admin_key: Optional[str] = Header(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_authorized = (
        (current_user and current_user.role in ("reviewer", "admin"))
        or (x_admin_key and x_admin_key == settings.ADMIN_API_KEY)
    )
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Designated reviewer access required to update reports.",
        )

    stmt = select(IssueReport).where(IssueReport.id == report_id)
    res = await db.execute(stmt)
    report = res.scalars().first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    new_status = body.status.upper()
    if new_status not in ("OPEN", "UNDER_REVIEW", "RESOLVED", "DISMISSED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be OPEN, UNDER_REVIEW, RESOLVED, or DISMISSED.",
        )

    report.status = new_status
    report.reviewer_notes = body.reviewer_notes.strip()
    if current_user:
        report.reviewer_id = current_user.id
    if new_status in ("RESOLVED", "DISMISSED"):
        report.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(report)

    # Notify student of resolution
    await create_notification(
        db=db,
        user_id=report.user_id,
        title=f"Report Update: {report.status}",
        message=f"Reviewer notes: {report.reviewer_notes}",
        event_type="REPORT_UPDATED",
        payload={"report_id": report.id, "status": report.status},
    )

    return IssueReportResponse.model_validate(report)
