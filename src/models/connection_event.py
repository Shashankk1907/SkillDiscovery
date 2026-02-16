from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime,Text
from src.config.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class ConnectionEvent(Base):
    __tablename__ = "connection_events"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    event_type= Column(String)