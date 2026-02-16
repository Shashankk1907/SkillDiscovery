from pydantic import BaseModel
from datetime import datetime


class SkillBase(BaseModel):
    name: str
    category: str
    description: str


class SkillCreate(SkillBase):
    pass

class SkillRead(SkillBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
