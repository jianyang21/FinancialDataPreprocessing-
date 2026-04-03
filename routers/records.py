from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, FinancialRecord, RecordType
from schemas import RecordCreateRequest, RecordUpdateRequest, RecordResponse, PaginatedRecords
from dependencies import require_viewer, require_analyst, require_admin

router = APIRouter()


@router.get("/", response_model=PaginatedRecords)
def list_records(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Records per page"),
    type: Optional[RecordType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category (partial match)"),
    start_date: Optional[datetime] = Query(None, description="Filter records on or after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter records on or before this date"),
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    query = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)

    if type:
        query = query.filter(FinancialRecord.type == type)
    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category}%"))
    if start_date:
        query = query.filter(FinancialRecord.date >= start_date)
    if end_date:
        query = query.filter(FinancialRecord.date <= end_date)

    total = query.count()
    records = (
        query.order_by(FinancialRecord.date.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {"total": total, "page": page, "limit": limit, "records": records}


@router.post("/", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    data: RecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    record = FinancialRecord(
        amount=data.amount,
        type=data.type,
        category=data.category,
        date=data.date,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{record_id}", response_model=RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_viewer),
):
    record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.patch("/{record_id}", response_model=RecordResponse)
def update_record(
    record_id: int,
    data: RecordUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_analyst),
):
    record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    updates = data.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(record, field, value)
    record.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    record.is_deleted = True
    db.commit()
