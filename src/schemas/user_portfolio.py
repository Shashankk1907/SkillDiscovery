from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class PortfolioItemType(str, Enum):
    project = "project"
    certificate = "certificate"
    work_sample = "work_sample"
    other = "other"


class UserPortfolioBase(BaseModel):
    title: str
    description: Optional[str] = None
    media_url: Optional[str] = None
    item_type: Optional[PortfolioItemType] = None


class UserPortfolioCreate(BaseModel):
    title: str
    description: Optional[str] = None
    media_url: Optional[str] = None
    item_type: str 


class UserPortfolioUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    media_url: Optional[str] = None
    item_type: Optional[PortfolioItemType] = None


class UserPortfolioRead(UserPortfolioBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
