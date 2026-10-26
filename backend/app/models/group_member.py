import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from backend.app.database import Base


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(
        String(36),
        ForeignKey("carpool_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    request_id = Column(
        String(36),
        ForeignKey("ride_requests.id", ondelete="SET NULL"),
        nullable=True,
    )

    acceptance_status = Column(
        String(20), default="PENDING", nullable=False
    )  # PENDING | ACCEPTED | DECLINED
    membership_status = Column(
        String(20), default="ACTIVE", nullable=False
    )  # ACTIVE | LEFT | CANCELLED

    fare_share_paise = Column(Integer, default=0, nullable=False)

    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )
