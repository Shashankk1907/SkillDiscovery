from pydantic import BaseModel, root_validator
from typing import Optional, Dict, List
from datetime import datetime
from src.schemas.user import UserRead
from src.schemas.skill import SkillRead

class SessionCreate(BaseModel):
    provider_id: int
    skill_id: int
    start_time: datetime
    end_time: datetime

    @root_validator(skip_on_failure=True)
    def check_times(cls, values):
        start, end = values.get('start_time'), values.get('end_time')
        if start and end and start >= end:
            raise ValueError('End time must be after start time')
        return values

class SessionRead(BaseModel):
    id: int
    requester_id: int
    provider_id: int
    skill_id: int
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
    
    # Optional expansions
    requester: Optional[UserRead] = None
    provider: Optional[UserRead] = None
    skill: Optional[SkillRead] = None

    class Config:
        orm_mode = True

class AvailabilityUpdate(BaseModel):
    availability: Dict[str, List[str]] 
    # Example: {"Monday": ["09:00-11:00", "14:00-16:00"], "Tuesday": []}
