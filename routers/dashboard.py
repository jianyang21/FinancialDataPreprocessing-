from collections import defaultdict
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import User, FinancialRecord, RecordType
from schemas import DashboardSummary, CategoryTotal, MonthlyTrend, RecordResponse
from dependencies import require_viewer, require_analyst

router = APIRouter()


def _base_query(db: Session, start_date: Optional[datetime], end_date: Optional[datetime]):
    q = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)
    if start_date:
        q = q.filter(FinancialRecord.date >= start_date)
    if end_date:
        q = q.filter(FinancialRecord.date <= end_date)
    return q


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    records = _base_query(db, start_date, end_date).all()

    total_income = sum(r.amount for r in records if r.type == RecordType.income)
    total_expenses = sum(r.amount for r in records if r.type == RecordType.expense)

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(total_income - total_expenses, 2),
        "record_count": len(records),
    }


@router.get("/categories", response_model=List[CategoryTotal])
def get_category_totals(
    type: Optional[RecordType] = Query(None, description="Filter by record type"),
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    query = (
        db.query(
            FinancialRecord.category,
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .filter(FinancialRecord.is_deleted == False)
    )

    if type:
        query = query.filter(FinancialRecord.type == type)

    results = query.group_by(FinancialRecord.category, FinancialRecord.type).all()

    return [
        {"category": r.category, "type": r.type, "total": round(r.total, 2), "count": r.count}
        for r in results
    ]


@router.get("/recent", response_model=List[RecordResponse])
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of recent records to return"),
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    return (
        db.query(FinancialRecord)
        .filter(FinancialRecord.is_deleted == False)
        .order_by(FinancialRecord.date.desc())
        .limit(limit)
        .all()
    )


@router.get("/trends", response_model=List[MonthlyTrend])
def get_monthly_trends(
    months: int = Query(6, ge=1, le=24, description="Number of past months to include"),
    db: Session = Depends(get_db),
    _: User = Depends(require_analyst),
):
    """Returns monthly income vs expense breakdown. Requires analyst or admin role."""
    records = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.is_deleted == False)
        .order_by(FinancialRecord.date.asc())
        .all()
    )

    # Group by YYYY-MM
    monthly: dict = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for r in records:
        key = r.date.strftime("%Y-%m")
        if r.type == RecordType.income:
            monthly[key]["income"] += r.amount
        else:
            monthly[key]["expenses"] += r.amount

    # Return the last N months, sorted
    sorted_months = sorted(monthly.keys())[-months:]

    return [
        {
            "month": month,
            "income": round(monthly[month]["income"], 2),
            "expenses": round(monthly[month]["expenses"], 2),
            "net": round(monthly[month]["income"] - monthly[month]["expenses"], 2),
        }
        for month in sorted_months
    ]
