from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.schemas.user import UserRead
from src.models.connection import ConnectionStatus

class ConnectionBase(BaseModel):
    pass

class ConnectionCreate(ConnectionBase):
    recipient_id: int

class ConnectionRead(ConnectionBase):
    id: int
    requester_id: int
    recipient_id: int
    status: ConnectionStatus
    created_at: datetime
    updated_at: datetime
    requester: Optional[UserRead] = None
    recipient: Optional[UserRead] = None

    class Config:
        orm_mode = True

class ConnectionUpdate(BaseModel):
    status: ConnectionStatus
