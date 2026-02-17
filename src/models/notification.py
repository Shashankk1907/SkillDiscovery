from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Boolean, String
from sqlalchemy.orm import relationship
from src.config.database import Base
from datetime import datetime

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False) # 'connection_request', 'message', 'session_invite', 'system'
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    related_entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id])
