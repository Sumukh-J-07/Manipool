import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from backend.app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(
        String(36),
        ForeignKey("carpool_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(String(36), nullable=False, index=True)
    sender_name = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
