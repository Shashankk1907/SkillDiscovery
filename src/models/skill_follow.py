from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.config.database import Base
from datetime import datetime

class SkillFollow(Base):
    __tablename__ = "skill_follows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    skill = relationship("Skill", foreign_keys=[skill_id])
