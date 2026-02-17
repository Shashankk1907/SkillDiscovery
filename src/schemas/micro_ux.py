from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.schemas.user import UserRead
from src.schemas.skill import SkillRead

class ReportCreate(BaseModel):
    reported_id: int
    reason: str
    details: Optional[str] = None

class ReportRead(BaseModel):
    id: int
    reporter_id: int
    reported_id: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

class SavedUserRead(BaseModel):
    id: int
    saved_user: UserRead
    created_at: datetime
    
    class Config:
        orm_mode = True

class SkillFollowRead(BaseModel):
    id: int
    skill: SkillRead
    created_at: datetime

    class Config:
        orm_mode = True
