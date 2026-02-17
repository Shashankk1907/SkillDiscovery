from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.config.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    intro_line = Column(String)
    profile_photo_url = Column(String, nullable=True)
    location_city = Column(String, index=True)
    location_country = Column(String)
    whatsapp_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    skills = relationship("UserSkill", back_populates="user")
    portfolio_items = relationship("UserPortfolio", back_populates="user")
    availability = Column(Text, nullable=True) # JSON string of weekly availability



