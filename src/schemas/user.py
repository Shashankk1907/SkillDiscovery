from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from src.schemas.user_skill import UserSkillRead
from src.schemas.user_portfolio import UserPortfolioRead
from src.models.connection import ConnectionStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    intro_line: Optional[str] = None
    profile_photo_url: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    whatsapp_number: Optional[str] = None
    is_superuser: Optional[bool] = False    

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    intro_line: Optional[str]
    profile_photo_url: Optional[str]
    location_city: Optional[str]
    location_country: Optional[str]
    whatsapp_number: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_superuser: Optional[bool] = False
    availability: Optional[str] = None

    class Config:
        orm_mode = True # Changed from from_attributes to orm_mode for Pydantic v1 compatibility if needed, or stick to v2 if environment supports

class UserProfileAggregated(BaseModel):
    user: UserRead
    skills: List[UserSkillRead]
    portfolio: List[UserPortfolioRead]
    connection_status: Optional[str] = "none" # "none", "pending_sent", "pending_received", "accepted", "rejected", "self"
    stats: Optional[dict] = None # e.g. {"views": 10, "connections": 5}
