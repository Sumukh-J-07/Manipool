from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class IssueReportCreate(BaseModel):
    text: str = Field(..., min_length=5, max_length=2000)
    category: str = Field("OTHER", description="SAFETY, NO_SHOW, PAYMENT, APP_ISSUE, OTHER")
    ride_id: Optional[str] = None
    group_id: Optional[str] = None


class IssueReportReviewUpdate(BaseModel):
    status: str = Field(..., description="UNDER_REVIEW, RESOLVED, DISMISSED")
    reviewer_notes: str = Field(..., min_length=2, max_length=2000)


class IssueReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    ride_id: Optional[str] = None
    group_id: Optional[str] = None
    text: str
    category: str
    status: str
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
