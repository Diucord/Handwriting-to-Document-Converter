from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, ConversionHistory
from schemas import HistoryResponse
from auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/", response_model=list[HistoryResponse])
def get_history(
    date: Optional[str] = Query(None, description="일별 필터 (YYYY-MM-DD)"),
    month: Optional[str] = Query(None, description="월별 필터 (YYYY-MM)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ConversionHistory).filter(ConversionHistory.user_id == user.id)

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(func.date(ConversionHistory.created_at) == target_date)
        except ValueError:
            pass

    elif month:
        try:
            target = datetime.strptime(month, "%Y-%m")
            query = query.filter(
                func.year(ConversionHistory.created_at) == target.year,
                func.month(ConversionHistory.created_at) == target.month,
            )
        except ValueError:
            pass

    return query.order_by(ConversionHistory.created_at.desc()).all()
