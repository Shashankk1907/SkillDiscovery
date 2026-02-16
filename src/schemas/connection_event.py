from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ConnectionEventRead(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    skill_id: int
    created_at: datetime

class ConnectionEventType(str, Enum):
    request = "request"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"

class ConnectionEventCreate(BaseModel):
    from_user_id: int
    to_user_id: int
    skill_id: int
    event_type: ConnectionEventType

    class Config:
        from_attributes = True
