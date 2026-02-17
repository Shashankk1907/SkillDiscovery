from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List
import json

from src.config.database import get_db
from src.models.user import User
from src.models.session import Session, SessionStatus
from src.schemas.session import SessionCreate, SessionRead, AvailabilityUpdate
from src.routes.users import get_current_user

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("/", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def book_session(
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.provider_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot book session with yourself")

    # Check overlaps (Simple check)
    overlap = db.query(Session).filter(
        (Session.provider_id == payload.provider_id) | (Session.requester_id == payload.provider_id),
        Session.status != SessionStatus.CANCELLED,
        Session.end_time > payload.start_time,
        Session.start_time < payload.end_time
    ).first()
    
    if overlap:
        raise HTTPException(status_code=400, detail="Time slot already booked")

    session = Session(
        requester_id=current_user.id,
        provider_id=payload.provider_id,
        skill_id=payload.skill_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=SessionStatus.PENDING.value
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/", response_model=List[SessionRead])
def get_my_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = db.query(Session).filter(
        (Session.requester_id == current_user.id) | (Session.provider_id == current_user.id)
    ).order_by(Session.start_time.asc()).all()
    return sessions

# User Availability Endpoint (placed here or users? task.md said users/me/availability but implementation plan listed it here too)
# Let's put it here but with path /users/me/availability re-routed? No, FastAPI router prefix is /sessions.
# Let's make it /sessions/availability for now or strictly follow task.md and put in users.py?
# Task md: PUT /users/me/availability.
# I will implement it in users.py to stick to the plan path, OR verify if I can serve it here.
# Let's put it in users.py or create a new router for it. users.py is getting large.
# Ideally, modifying user data belongs in users.py. But availability is session-specific.
# I'll implement `PUT /users/me/availability` locally in users.py or redirect.
# Let's stick to adding it to `src/routes/users.py` as it modifies the User model directly.
