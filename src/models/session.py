from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, String
from sqlalchemy.orm import relationship
from src.config.database import Base
from datetime import datetime
import enum

class SessionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, default=SessionStatus.PENDING) 
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    provider = relationship("User", foreign_keys=[provider_id])
    skill = relationship("Skill")
