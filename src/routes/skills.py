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
