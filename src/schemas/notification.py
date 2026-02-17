from pydantic import BaseModel
from datetime import datetime

class NotificationRead(BaseModel):
    id: int
    type: str
    content: str
    is_read: bool
    created_at: datetime
    related_entity_id: int = None

    class Config:
        orm_mode = True
