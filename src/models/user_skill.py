from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime,Text
from src.config.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    role= Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    teaching_style = Column(String)
    experience_note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship(
        "User",
        back_populates="skills"
    )

