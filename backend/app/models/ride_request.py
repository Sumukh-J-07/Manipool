import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from backend.app.database import Base


class RideRequest(Base):
    __tablename__ = "ride_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    pickup_id = Column(String(50), nullable=False)
    pickup_name = Column(String(100), nullable=False)
    pickup_area = Column(String(100), nullable=False)
    pickup_lat = Column(Float, nullable=True)
    pickup_lng = Column(Float, nullable=True)

    destination_id = Column(String(50), nullable=False)
    destination_name = Column(String(100), nullable=False)
    destination_area = Column(String(100), nullable=False)
    destination_corridor = Column(String(50), nullable=False)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)

    departure = Column(DateTime, nullable=False, index=True)
    flexibility = Column(Integer, default=30, nullable=False)  # 0, 15, 30, 45

    status = Column(String(30), default="SEARCHING", nullable=False, index=True)
    group_id = Column(String(36), ForeignKey("carpool_groups.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
