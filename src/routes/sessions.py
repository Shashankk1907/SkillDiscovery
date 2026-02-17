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

from datetime import datetime

@router.get("/", response_model=List[SessionRead])
def get_my_sessions(
    status: str = None,
    role: str = None,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Session).filter(
        (Session.requester_id == current_user.id) | (Session.provider_id == current_user.id)
    )

    if status:
        # Validate status if strict, or just filter
        query = query.filter(Session.status == status)
    
    if role:
        if role == "provider":
            query = query.filter(Session.provider_id == current_user.id)
        elif role == "requester":
            query = query.filter(Session.requester_id == current_user.id)
            
    sessions = query.order_by(Session.start_time.asc()).all()
    return sessions

@router.get("/upcoming", response_model=List[SessionRead])
def get_upcoming_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    sessions = db.query(Session).filter(
        (Session.requester_id == current_user.id) | (Session.provider_id == current_user.id),
        Session.start_time > now,
        Session.status.notin_([SessionStatus.CANCELLED.value, SessionStatus.REJECTED.value])
    ).order_by(Session.start_time.asc()).all()
    return sessions

@router.get("/past", response_model=List[SessionRead])
def get_past_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    sessions = db.query(Session).filter(
        (Session.requester_id == current_user.id) | (Session.provider_id == current_user.id),
        Session.end_time < now
    ).order_by(Session.start_time.desc()).all()
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

@router.put("/{session_id}/accept", response_model=SessionRead)
def accept_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the provider can accept this session")

    if session.status != SessionStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot accept session with status {session.status}")

    session.status = SessionStatus.ACCEPTED.value
    db.commit()
    db.refresh(session)
    return session

@router.put("/{session_id}/reject", response_model=SessionRead)
def reject_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the provider can reject this session")

    if session.status != SessionStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot reject session with status {session.status}")

    session.status = SessionStatus.REJECTED.value
    db.commit()
    db.refresh(session)
    return session

@router.put("/{session_id}/cancel", response_model=SessionRead)
def cancel_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.id not in [session.requester_id, session.provider_id]:
        raise HTTPException(status_code=403, detail="You are not a participant in this session")

    if session.status in [SessionStatus.CANCELLED.value, SessionStatus.COMPLETED.value, SessionStatus.REJECTED.value]:
         raise HTTPException(status_code=400, detail=f"Cannot cancel session with status {session.status}")

    session.status = SessionStatus.CANCELLED.value
    db.commit()
    db.refresh(session)
    return session

@router.put("/{session_id}/complete", response_model=SessionRead)
def complete_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the provider can mark this session as completed")

    if session.status != SessionStatus.ACCEPTED.value:
        raise HTTPException(status_code=400, detail="Only accepted sessions can be completed")
    
    session.status = SessionStatus.COMPLETED.value
    db.commit()
    db.refresh(session)
    return session
