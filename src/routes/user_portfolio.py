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
