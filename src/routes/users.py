from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from src.schemas.user import UserCreate, UserRead, UserProfileAggregated
from src.models.user import User
from src.models.user_skill import UserSkill
from src.models.connection import Connection, ConnectionStatus
from src.config.database import get_db
from src.models.profile_view import ProfileView
from src.schemas.dashboard import DashboardStats
from src.schemas.session import AvailabilityUpdate
from sqlalchemy import func
import json
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


from fastapi.security import OAuth2PasswordRequestForm
from src.auth.jwt import create_access_token, verify_token, oauth2_scheme
from src.schemas.token import Token
from datetime import timedelta
import os

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    try:
        email = verify_token(token, None) # We need verify_token to accept None for exception or handle it
        if not email:
            return None
        user = db.query(User).filter(User.email == email).first()
        return user
    except:
        return None


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered")

    user = User(
        email=user_in.email,
        password=hash_password(user_in.password),
        name=user_in.name,
        intro_line=user_in.intro_line,
        profile_photo_url=user_in.profile_photo_url,
        location_city=user_in.location_city,
        location_country=user_in.location_country,
        whatsapp_number=user_in.whatsapp_number,
        is_active=True,
        is_superuser=user_in.is_superuser if hasattr(user_in, 'is_superuser') else False,
)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    return current_user





@router.get("/search", response_model=List[UserRead])
def search_users(
    name: Optional[str] = None,
    city: Optional[str] = None,
    skill_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(User).filter(User.is_active == True)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    
    if city:
        query = query.filter(User.location_city.ilike(f"%{city}%"))

    if skill_id:
        query = query.join(UserSkill).filter(UserSkill.skill_id == skill_id)

    return query.offset(skip).limit(limit).all()


@router.get("/{user_id}/profile", response_model=UserProfileAggregated)
def get_user_profile(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional) # Need to implement optional auth
):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log Profile View
    if current_user and current_user.id != user_id:
        view = ProfileView(viewer_id=current_user.id, viewed_id=user_id)
        db.add(view)
        db.commit()

    connection_status = "none"
    if current_user:
        if current_user.id == user_id:
             connection_status = "self"
        else:
            # Check connection
            conn = db.query(Connection).filter(
                ((Connection.requester_id == current_user.id) & (Connection.recipient_id == user_id)) |
                ((Connection.requester_id == user_id) & (Connection.recipient_id == current_user.id))
            ).first()
            
            if conn:
                if conn.status == ConnectionStatus.ACCEPTED:
                    connection_status = "accepted"
                elif conn.status == ConnectionStatus.REJECTED:
                    connection_status = "rejected"
                elif conn.status == ConnectionStatus.PENDING:
                    if conn.requester_id == current_user.id:
                        connection_status = "pending_sent"
                    else:
                        connection_status = "pending_received"

    return {
        "user": user,
        "skills": user.skills,
        "portfolio": user.portfolio_items,
        "portfolio": user.portfolio_items,
        "connection_status": connection_status,
        "stats": {
            "views": db.query(ProfileView).filter(ProfileView.viewed_id == user_id).count(),
            # connections count not easily available without filtering Connection table or adding relationship
            "connections": 0 # Placeholder or implement count query
        }
    }


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
@router.get("/", response_model=List[UserRead])
def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),):
    users = db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    return users


@router.put("/me", response_model=UserRead)
def update_my_profile(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    current_user.name = user_in.name
    current_user.intro_line = user_in.intro_line
    current_user.profile_photo_url = user_in.profile_photo_url
    current_user.location_city = user_in.location_city
    current_user.location_country = user_in.location_country
    current_user.whatsapp_number = user_in.whatsapp_number

    if user_in.password:
        current_user.password = hash_password(user_in.password)

    db.commit()
    db.refresh(current_user)
    return current_user


    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/availability", response_model=UserRead)
def update_availability(
    payload: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.availability = json.dumps(payload.availability)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    current_user.is_active = False
    db.commit()

@router.get("/me/completion")
def get_profile_completion(current_user: User = Depends(get_current_user)):
    fields = {
        "profile_photo": current_user.profile_photo_url,
        "intro_line": current_user.intro_line,
        "location": current_user.location_city,
        "whatsapp": current_user.whatsapp_number,
        "skills": current_user.skills
    }
    
    completed = [k for k, v in fields.items() if v]
    percentage = int((len(completed) / len(fields)) * 100)
    missing = [k for k, v in fields.items() if not v]
    
    return {"percentage": percentage, "missing": missing}

from src.schemas.user_skill import UserSkillCreate, UserSkillRead, SkillRole

@router.post("/me/skills", response_model=UserSkillRead, status_code=status.HTTP_201_CREATED)
def add_my_skill(
    payload: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Override user_id to current_user.id to ensure security
    payload.user_id = current_user.id
    
    # Check if skill exists (optional, depends on if we allowed creating skills on fly, but schema has skill_id)
    # If payload deals with skill_id:
    
    existing = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == payload.skill_id,
        UserSkill.role == payload.role
    ).first()
    
    if existing:
         raise HTTPException(status_code=400, detail="Skill already added")
         
    user_skill = UserSkill(**payload.dict())
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)
    return user_skill

@router.get("/me/suggested-mentors", response_model=List[UserRead])
def get_suggested_mentors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get skills I want to learn
    learn_skills = [s.skill_id for s in current_user.skills if s.role == SkillRole.learn]
    
    if not learn_skills:
        return []
        
    # 2. Find users who teach these skills
    # We want users who have a UserSkill entry with role='teach' and skill_id in learn_skills
    # And are NOT me
    
    mentors = (
        db.query(User)
        .join(UserSkill)
        .filter(
            User.id != current_user.id,
            User.is_active == True,
            UserSkill.role == SkillRole.teach,
            UserSkill.skill_id.in_(learn_skills)
        )
        .distinct()
        .limit(10)
        .all()
    )
    
    return mentors
    return mentors

@router.get("/me/dashboard", response_model=DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Pending Requests (Received)
    pending_requests = db.query(Connection).filter(
        Connection.recipient_id == current_user.id,
        Connection.status == ConnectionStatus.PENDING
    ).count()
    
    # 2. New Connections (Accepted recently? Or just total for now)
    # Let's just return total connections for simplicity or query accepted ones
    new_connections = db.query(Connection).filter(
        ((Connection.requester_id == current_user.id) | (Connection.recipient_id == current_user.id)),
        Connection.status == ConnectionStatus.ACCEPTED
    ).count()
    
    # 3. Profile Views
    profile_views = db.query(ProfileView).filter(ProfileView.viewed_id == current_user.id).count()
    
    # 4. Endorsements - Placeholder as UserSkill doesn't have endorsements count yet (or we query related table if exists)
    # Checking models... UserSkill has id, role, experience... no endorsement count column yet?
    # Actually request says "Endorse Skill" endpoint is Step 6. So for now 0.
    skill_endorsements = 0
    
    # 5. Suggested Connections (Reuse mentor logic)
    suggested = get_suggested_mentors(db, current_user)
    
    return {
        "pending_requests": pending_requests,
        "new_connections": new_connections,
        "profile_views": profile_views,
        "skill_endorsements": skill_endorsements,
        "suggested_connections": suggested
    }

@router.get("/me/profile-views", response_model=List[UserRead])
def get_my_profile_views(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get users who viewed my profile
    # Join ProfileView with User
    viewers = (
        db.query(User)
        .join(ProfileView, ProfileView.viewer_id == User.id)
        .filter(ProfileView.viewed_id == current_user.id)
        .order_by(ProfileView.viewed_at.desc())
        .limit(20) # Limit to recent 20
        .all()
    )
    return viewers

# Micro-UX: Save/Unsave User
from src.models.saved_user import SavedUser
from src.schemas.micro_ux import SavedUserRead

@router.post("/{user_id}/save", status_code=status.HTTP_200_OK)
def toggle_save_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot save yourself")
        
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
        
    existing = db.query(SavedUser).filter(
        SavedUser.user_id == current_user.id,
        SavedUser.saved_user_id == user_id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "User unsaved"}
    else:
        saved = SavedUser(user_id=current_user.id, saved_user_id=user_id)
        db.add(saved)
        db.commit()
        return {"message": "User saved"}

@router.get("/me/saved", response_model=List[SavedUserRead])
def get_saved_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved = db.query(SavedUser).filter(
        SavedUser.user_id == current_user.id
    ).order_by(SavedUser.created_at.desc()).all()
    return saved
    saved = db.query(SavedUser).filter(
        SavedUser.user_id == current_user.id
    ).order_by(SavedUser.created_at.desc()).all()
    return saved


# Connection Lists
@router.get("/{user_id}/connections", response_model=List[UserRead])
def get_user_connections(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # visibility check? roughly public profile feature
):
    # Get accepted connections for user_id
    connections = db.query(Connection).filter(
        ((Connection.requester_id == user_id) | (Connection.recipient_id == user_id)),
        Connection.status == ConnectionStatus.ACCEPTED
    ).all()
    
    connected_user_ids = set()
    for c in connections:
        if c.requester_id == user_id:
            connected_user_ids.add(c.recipient_id)
        else:
            connected_user_ids.add(c.requester_id)
            
    if not connected_user_ids:
        return []
        
    return db.query(User).filter(User.id.in_(connected_user_ids)).all()

@router.get("/{user_id}/connections/mutual", response_model=List[UserRead])
def get_mutual_connections(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        return [] # No mutuals with self
        
    # 1. My connections
    my_conns = db.query(Connection).filter(
        ((Connection.requester_id == current_user.id) | (Connection.recipient_id == current_user.id)),
        Connection.status == ConnectionStatus.ACCEPTED
    ).all()
    
    my_ids = set()
    for c in my_conns:
        my_ids.add(c.recipient_id if c.requester_id == current_user.id else c.requester_id)
        
    # 2. Their connections
    their_conns = db.query(Connection).filter(
        ((Connection.requester_id == user_id) | (Connection.recipient_id == user_id)),
        Connection.status == ConnectionStatus.ACCEPTED
    ).all()
    
    their_ids = set()
    for c in their_conns:
        their_ids.add(c.recipient_id if c.requester_id == user_id else c.requester_id)
        
    # 3. Intersection
    mutual_ids = my_ids.intersection(their_ids)
    
    if not mutual_ids:
        return []
        
    return db.query(User).filter(User.id.in_(mutual_ids)).all()
