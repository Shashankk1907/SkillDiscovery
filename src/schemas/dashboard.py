from pydantic import BaseModel
from typing import List, Optional
from src.schemas.user import UserRead

class DashboardStats(BaseModel):
    pending_requests: int
    new_connections: int
    profile_views: int
    skill_endorsements: int
    suggested_connections: List[UserRead]
