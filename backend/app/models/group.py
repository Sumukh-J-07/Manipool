import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from backend.app.database import Base


class CarpoolGroup(Base):
    __tablename__ = "carpool_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(
        String(30), default="WAITING_FOR_ACCEPTANCE", nullable=False, index=True
    )  # WAITING_FOR_ACCEPTANCE, GROUP_FORMED, RIDE_BOOKED, IN_PROGRESS, COMPLETED, CANCELLED

    pickup_mode = Column(String(20), default="common", nullable=False)  # common | sequential
    meeting_point_id = Column(String(50), default="campus", nullable=False)
    meeting_point_name = Column(String(100), default="Campus Main Gate", nullable=False)

    departure_time = Column(DateTime, nullable=False)
    destination_id = Column(String(50), nullable=False)
    destination_name = Column(String(100), nullable=False)

    vehicle_type = Column(String(20), default="cab", nullable=False)  # cab | auto
    vehicle_capacity = Column(Integer, default=4, nullable=False)
    total_fare_paise = Column(Integer, default=84000, nullable=False)

    booked_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    confirmed_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
