from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from src.schemas.user import UserRead

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewRead(BaseModel):
    id: int
    author_id: int
    subject_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    author: Optional[UserRead] = None # For display

    class Config:
        orm_mode = True
