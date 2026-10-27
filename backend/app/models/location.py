import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, String
from backend.app.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    area = Column(String(100), nullable=False)
    kind = Column(String(30), default="campus", nullable=False)  # campus | transit | commercial | city | custom
    corridor = Column(String(30), default="campus", nullable=False, index=True)  # campus | airport | central | north | west | custom
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
