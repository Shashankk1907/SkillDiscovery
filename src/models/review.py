from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, CheckConstraint
from sqlalchemy.orm import relationship
from src.config.database import Base
from datetime import datetime

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )

    # Relationships
    author = relationship("User", foreign_keys=[author_id])
    subject = relationship("User", foreign_keys=[subject_id])
