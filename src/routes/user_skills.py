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
