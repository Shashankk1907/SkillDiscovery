# ===== auth.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.models.user import User
from src.schemas.user import UserCreate, UserRead
from src.schemas.token import Token, RefreshTokenInput
from src.auth.jwt import create_access_token, create_refresh_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from src.routes.users import hash_password, verify_password
from datetime import timedelta
from jose import jwt, JWTError
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

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
    
    refresh_token = create_refresh_token(
        data={"sub": user.email}
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(token_in: RefreshTokenInput, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token_in.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "refresh":
            raise credentials_exception
            
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        # Rotate refresh token? Typically yes, but for simplicity we can return a new one or keep old.
        # Let's issue a new one to enable rotation.
        new_refresh_token = create_refresh_token(
            data={"sub": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise credentials_exception

@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}


# ===== sessions.py =====
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


# ===== reviews.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.models.user import User
from src.models.review import Review
from src.routes.users import get_current_user, get_user # Reuse get_user to check existence
from src.schemas.review import ReviewCreate, ReviewRead

router = APIRouter(tags=["Reviews"])

@router.post("/users/{user_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def leave_review(
    user_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already reviewed? (Optional, let's allow multiple for now or restrict to one)
    # Let's restrict to one review per author-subject pair for simplicity of "trust"
    existing = db.query(Review).filter(
        Review.author_id == current_user.id,
        Review.subject_id == user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this user")

    review = Review(
        author_id=current_user.id,
        subject_id=user_id,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@router.get("/users/{user_id}/reviews", response_model=List[ReviewRead])
def get_user_reviews(
    user_id: int,
    db: Session = Depends(get_db),
):
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    reviews = db.query(Review).filter(Review.subject_id == user_id).order_by(Review.created_at.desc()).all()
    return reviews


# ===== skills.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from src.config.database import get_db
from src.models.skill import Skill
from src.schemas.skill import SkillCreate, SkillRead
from src.routes.users import get_current_user 
from src.models.user import User


router = APIRouter(prefix="/skills", tags=["Skills"])

@router.get("/suggestions", response_model=List[SkillRead])
def suggest_skills(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    if not query:
        return []
        
    skills = (
        db.query(Skill)
        .filter(Skill.name.ilike(f"%{query}%"))
        .limit(limit)
        .all()
    )
    return skills

# Micro-UX: Follow Skill
from src.models.skill_follow import SkillFollow

@router.post("/{skill_id}/follow", status_code=status.HTTP_200_OK)
def toggle_follow_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
        
    existing = db.query(SkillFollow).filter(
        SkillFollow.user_id == current_user.id,
        SkillFollow.skill_id == skill_id
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Skill unfollowed"}
    else:
        follow = SkillFollow(user_id=current_user.id, skill_id=skill_id)
        db.add(follow)
        db.commit()
        return {"message": "Skill followed"}


@router.post("/", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to create new skills")

    normalized_name = payload.name.strip().lower()

    existing = (
        db.query(Skill)
        .filter(Skill.name.ilike(normalized_name))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Skill already exists",
        )

    skill = Skill(
        name=normalized_name,
        category=payload.category,
        description=payload.description,)

    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill

@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Skill.category).distinct().all()
    return [c[0] for c in categories if c[0]]

@router.get("/", response_model=List[SkillRead])
def list_skills(
    skill: Optional[str] = Query(None, description="Search skill"),
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Skill)

    if skill:
        query = query.filter(Skill.name.ilike(f"%{skill.lower()}%"))

    if category:
        query = query.filter(Skill.category.ilike(f"%{category}%"))

    return (
        query
        .order_by(Skill.name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

@router.get("/{skill_id}", response_model=SkillRead)
def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()

    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    db.delete(skill)
    db.commit()


# ===== users.py =====
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


# ===== connections.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.config.database import get_db
from src.models import Connection, User, ConnectionStatus
from src.schemas.connection import ConnectionCreate, ConnectionRead, ConnectionUpdate
from src.routes.users import get_current_user
from src.routes.notifications import create_notification_internal

router = APIRouter(prefix="/connections", tags=["Connections"])

@router.post("/", response_model=ConnectionRead, status_code=status.HTTP_201_CREATED)
def send_connection_request(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot connect with yourself")

    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(Connection).filter(
        ((Connection.requester_id == current_user.id) & (Connection.recipient_id == payload.recipient_id)) |
        ((Connection.requester_id == payload.recipient_id) & (Connection.recipient_id == current_user.id))
    ).first()

    if existing:
        if existing.status == ConnectionStatus.PENDING:
            raise HTTPException(status_code=400, detail="Connection request already pending")
        elif existing.status == ConnectionStatus.ACCEPTED:
            raise HTTPException(status_code=400, detail="Already connected")
        elif existing.status == ConnectionStatus.REJECTED:
             # Allow re-requesting if rejected? For now, yes, maybe update status to pending.
             existing.status = ConnectionStatus.PENDING
             existing.requester_id = current_user.id # Reset requester
             existing.recipient_id = payload.recipient_id
             db.commit()
             db.refresh(existing)
             return existing
        
    new_connection = Connection(
        requester_id=current_user.id,
        recipient_id=payload.recipient_id,
        status=ConnectionStatus.PENDING
    )
    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)
    
    # Notify recipient
    create_notification_internal(
        db=db,
        recipient_id=payload.recipient_id,
        type="connection_request",
        content=f"{current_user.name} sent you a connection request.",
        related_entity_id=new_connection.id
    )
    
    return new_connection

@router.delete("/{connection_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_connection_request(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.requester_id == current_user.id,
        Connection.status == ConnectionStatus.PENDING
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Pending connection request not found")
        
    db.delete(connection)
    db.commit()

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Allow removing if user is either requester or recipient
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        ((Connection.requester_id == current_user.id) | (Connection.recipient_id == current_user.id))
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    db.delete(connection)
    db.commit()

@router.get("/requests", response_model=List[ConnectionRead])
def get_pending_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Connection).filter(
        Connection.recipient_id == current_user.id,
        Connection.status == ConnectionStatus.PENDING
    ).all()

@router.put("/{connection_id}", response_model=ConnectionRead)
def update_connection_status(
    connection_id: int,
    payload: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    if connection.recipient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this connection")

    if payload.status not in [ConnectionStatus.ACCEPTED, ConnectionStatus.REJECTED]:
         raise HTTPException(status_code=400, detail="Invalid status update")

    connection.status = payload.status
    db.commit()
    db.refresh(connection)
    return connection

@router.get("/", response_model=List[ConnectionRead])
def get_connections(
    type: str = Query("accepted", regex="^(accepted|pending|sent)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Connection)
    
    if type == "accepted":
        query = query.filter(
            ((Connection.requester_id == current_user.id) | (Connection.recipient_id == current_user.id)),
            Connection.status == ConnectionStatus.ACCEPTED
        )
    elif type == "pending":
        # Received Pending Requests
        query = query.filter(
            Connection.recipient_id == current_user.id,
            Connection.status == ConnectionStatus.PENDING
        )
    elif type == "sent":
        # Sent Pending Requests
        query = query.filter(
            Connection.requester_id == current_user.id,
            Connection.status == ConnectionStatus.PENDING
        )
        
    return query.all()


# ===== __init__.py =====
from src.routes.users import router as users
#from app.routers.skills import router as skills
#from app.routers.user_skills import router as user_skills
#from app.routers.connection_events import router as connection_events

__all__ = [
    "users"
    #"skills",
    #"user_skills",
    #"connection_events",
]


# ===== user_skills.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional,Text
from src.config.database import get_db
from src.models.user_skill import UserSkill
from src.models.skill import Skill
from src.models.user import User
from src.schemas.user_skill import UserSkillCreate, UserSkillRead, SkillRole
from src.routes.users import get_current_user 

router = APIRouter(prefix="/user-skills", tags=["User Skills"])


@router.post("/", response_model=UserSkillRead, status_code=status.HTTP_201_CREATED)
def add_user_skill(
    payload: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot add skill for another user")

    skill = db.query(Skill).filter(Skill.id == payload.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    existing = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == payload.user_id,
            UserSkill.skill_id == payload.skill_id,
            UserSkill.role == payload.role,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Skill already added")

    user_skill = UserSkill(**payload.dict())
    db.add(user_skill)
    db.commit()
    db.refresh(user_skill)
    return user_skill

@router.get("/me", response_model=List[UserSkillRead])
def get_my_skills(
    role: Optional[SkillRole] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(UserSkill).filter(UserSkill.user_id == current_user.id)

    if role:
        query = query.filter(UserSkill.role == role)

    return query.all()

@router.get("/user/{user_id}", response_model=List[UserSkillRead])
def get_user_public_skills(
    user_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.role == SkillRole.teach        )
        .all()
    )

@router.get("/mentors", response_model=List[UserSkillRead])
def discover_mentors(
    skill_id: Optional[int] = None,
    city: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = (
        db.query(UserSkill)
        .join(User, UserSkill.user_id == User.id)
        .filter(
            UserSkill.role == SkillRole.teach,
            User.is_active == True
        )
    )

    if skill_id:
        query = query.filter(UserSkill.skill_id == skill_id)

    if city:
        query = query.filter(User.location_city.ilike(f"%{city}%"))

    return query.offset(skip).limit(limit).all()


@router.put("/{user_skill_id}", response_model=UserSkillRead)
def update_user_skill(
    user_skill_id: int,
    payload: UserSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id).first()

    if not user_skill:
        raise HTTPException(status_code=404, detail="User skill not found")

    if user_skill.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    for field, value in payload.dict(exclude={"user_id", "skill_id"}).items():
        setattr(user_skill, field, value)

    db.commit()
    db.refresh(user_skill)
    return user_skill

@router.delete("/{user_skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_skill(
    user_skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id).first()

    if not user_skill:
        raise HTTPException(status_code=404, detail="User skill not found")

    if user_skill.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(user_skill)
    db.commit()


# ===== user_portfolio.py =====
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.config.database import get_db
from src.models.user_portfolio import UserPortfolio
from src.models.user import User
from src.schemas.user_portfolio import (
    UserPortfolioCreate,
    UserPortfolioRead,
    UserPortfolioUpdate,
)
from src.routes.users import get_current_user


router = APIRouter(prefix="/portfolio", tags=["User Portfolio"])


@router.post("/me", response_model=UserPortfolioRead, status_code=status.HTTP_201_CREATED)
def create_portfolio_item(
    payload: UserPortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = UserPortfolio(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        media_url=payload.media_url,
        item_type=payload.item_type,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/me", response_model=List[UserPortfolioRead])
def get_my_portfolio(
    item_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(UserPortfolio).filter(
        UserPortfolio.user_id == current_user.id
    )

    if item_type:
        query = query.filter(UserPortfolio.item_type == item_type)

    return query.order_by(UserPortfolio.created_at.desc()).all()


@router.get("/user/{user_id}", response_model=List[UserPortfolioRead])
def get_user_public_portfolio(
    user_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(UserPortfolio)
        .filter(UserPortfolio.user_id == user_id)
        .order_by(UserPortfolio.created_at.desc())
        .all()
    )


@router.put("/{portfolio_id}", response_model=UserPortfolioRead)
def update_portfolio_item(
    portfolio_id: int,
    payload: UserPortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(UserPortfolio).filter(UserPortfolio.id == portfolio_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_item(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(UserPortfolio).filter(UserPortfolio.id == portfolio_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found")

    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(item)
    db.commit()


# ===== reports.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.config.database import get_db
from src.models.user import User
from src.models.report import Report
from src.schemas.micro_ux import ReportCreate, ReportRead
from src.routes.users import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("/users", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def report_user(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.reported_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
        
    target = db.query(User).filter(User.id == payload.reported_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
        
    report = Report(
        reporter_id=current_user.id,
        reported_id=payload.reported_id,
        reason=payload.reason,
        details=payload.details
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


# ===== notifications.py =====
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


# ===== uploads.py =====
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
from typing import List

from src.schemas.user import UserRead
from src.routes.users import get_current_user, get_db
from src.models.user import User
from sqlalchemy.orm import Session # Fixed import

router = APIRouter(prefix="/upload", tags=["Uploads"])

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user), # Require auth for uploads
):
    try:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return the relative URL that can be served by StaticFiles
        return {"url": f"/static/uploads/{unique_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")


# ===== users_imports_temp.py =====
from src.models.profile_view import ProfileView
from src.schemas.dashboard import DashboardStats
from sqlalchemy import func


# ===== messaging.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.config.database import get_db
from src.models.user import User
from src.models.conversation import Conversation
from src.models.message import Message
from src.routes.users import get_current_user
from src.schemas.messaging import ConversationRead, ConversationCreate, MessageRead, MessageCreate

router = APIRouter(prefix="/messaging", tags=["Messaging"]) # Changed prefix to /messaging to avoid conflict or clarify? Plan said /conversations and /messages. Let's stick to Plan but maybe group under messaging tag.

# Let's use /conversations for conversation management
# and /messages for sending? Or keep them all under one router.

@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def start_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.recipient_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot find conversation with yourself") # Logic: usually ppl talk to others

    # Check if exists
    conversation = db.query(Conversation).filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == payload.recipient_id)) |
        ((Conversation.user1_id == payload.recipient_id) & (Conversation.user2_id == current_user.id))
    ).first()

    if conversation:
        return conversation

    # Create new
    conversation = Conversation(
        user1_id=current_user.id,
        user2_id=payload.recipient_id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@router.get("/conversations", response_model=List[ConversationRead])
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch conversations where I am user1 or user2
    conversations = db.query(Conversation).filter(
        (Conversation.user1_id == current_user.id) | (Conversation.user2_id == current_user.id)
    ).order_by(Conversation.updated_at.desc()).all()
    
    # We need to populate last_message manually or via join if not eager loaded
    # Pydantic schema expects last_message. 
    # Let's let helper method or Pydantic allow None, but valid UI needs it.
    # For now, simplistic approach.
    
    return conversations

@router.post("/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify conversation participation
    conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not a participant")
        
    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=payload.content
    )
    db.add(message)
    
    # Update conversation updated_at
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    return message

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageRead])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if conversation.user1_id != current_user.id and conversation.user2_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not a participant")
        
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.sent_at.asc()).all()
    
    return messages

