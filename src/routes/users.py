from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from src.schemas.user import UserCreate, UserRead, UserProfileAggregated
from src.models.user import User
from src.models.user_skill import UserSkill
from src.models.connection import Connection, ConnectionStatus
from src.config.database import get_db
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
        "connection_status": connection_status
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



@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),):
    current_user.is_active = False
    db.commit()
