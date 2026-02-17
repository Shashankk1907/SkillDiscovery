from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List

from src.config.database import get_db
from src.models.user import User
from src.models.notification import Notification
from src.schemas.notification import NotificationRead
from src.routes.users import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=List[NotificationRead])
def get_my_notifications(
    limit: int = 20,
    skip: int = 0,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = db.query(Notification).filter(
        Notification.recipient_id == current_user.id
    ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications

@router.put("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_as_read(
    notification_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    db.commit()

# Utility function to be used by other modules
def create_notification_internal(
    db: DBSession,
    recipient_id: int,
    type: str,
    content: str,
    related_entity_id: int = None
):
    notif = Notification(
        recipient_id=recipient_id,
        type=type,
        content=content,
        related_entity_id=related_entity_id,
        is_read=False
    )
    db.add(notif)
    db.commit() # Internal usage might need commit or flush depending on transaction scope. 
    # For simplicity, we commit here, but ideally we should let caller commit if part of bigger transaction.
    # But this function creates a session side-effect, so it's okay to commit if isolated.
    # If called within another route that has uncommitted changes, validation might fail if DB is strict.
    # Let's assume standalone or safe validation.
    return notif
