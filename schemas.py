import re
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from models import UserRole, RecordType


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

    @validator("email")
    def email_valid(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email address")
        return v.lower()

    @validator("password")
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Users ─────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class UserCreateRequest(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.viewer

    @validator("email")
    def email_valid(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email address")
        return v.lower()


class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ── Financial Records ─────────────────────────────────────────────────────────

class RecordCreateRequest(BaseModel):
    amount: float
    type: RecordType
    category: str
    date: datetime
    notes: Optional[str] = None

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v

    @validator("category")
    def category_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Category cannot be empty")
        return v.strip()


class RecordUpdateRequest(BaseModel):
    amount: Optional[float] = None
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: str
    date: datetime
    notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class PaginatedRecords(BaseModel):
    total: int
    page: int
    limit: int
    records: List[RecordResponse]


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    record_count: int


class CategoryTotal(BaseModel):
    category: str
    type: RecordType
    total: float
    count: int


class MonthlyTrend(BaseModel):
    month: str  # "YYYY-MM"
    income: float
    expenses: float
    net: float
