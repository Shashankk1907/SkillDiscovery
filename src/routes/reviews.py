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
