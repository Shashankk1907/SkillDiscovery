from sqlalchemy import Column, Integer, ForeignKey, DateTime
from src.config.database import Base
from datetime import datetime

class ProfileView(Base):
    __tablename__ = "profile_views"

    id = Column(Integer, primary_key=True, index=True)
    viewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    viewed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    viewed_at = Column(DateTime, default=datetime.utcnow)
