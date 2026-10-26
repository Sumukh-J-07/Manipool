import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from backend.app.database import Base


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ride_id = Column(String(36), nullable=True)
    group_id = Column(String(36), nullable=True)

    text = Column(Text, nullable=False)
    category = Column(
        String(30), default="OTHER", nullable=False
    )  # SAFETY | NO_SHOW | PAYMENT | APP_ISSUE | OTHER
    status = Column(
        String(20), default="OPEN", nullable=False, index=True
    )  # OPEN | UNDER_REVIEW | RESOLVED | DISMISSED

    reviewer_id = Column(String(36), nullable=True)
    reviewer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
