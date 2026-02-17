from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.schemas.user import UserRead

class MessageCreate(BaseModel):
    conversation_id: int
    content: str

class MessageRead(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    sent_at: datetime

    class Config:
        orm_mode = True

class ConversationCreate(BaseModel):
    recipient_id: int

class ConversationRead(BaseModel):
    id: int
    user1: UserRead
    user2: UserRead
    last_message: Optional[MessageRead] = None
    updated_at: datetime

    class Config:
        orm_mode = True
