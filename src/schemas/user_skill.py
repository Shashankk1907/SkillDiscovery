from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SkillRole(str, Enum):
    teach = "teach"
    learn = "learn"


class UserSkillBase(BaseModel):
    role: SkillRole
    teaching_style: Optional[str] = None
    experience_note: Optional[str] = None


class UserSkillCreate(UserSkillBase):
    user_id: int
    skill_id: int

class UserSkillRead(UserSkillBase):
    id: int
    user_id: int
    skill_id: int
    created_at: datetime

    class Config:
        from_attributes = True
