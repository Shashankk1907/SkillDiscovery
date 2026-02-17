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
