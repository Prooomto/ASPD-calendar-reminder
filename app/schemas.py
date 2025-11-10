from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: Optional[str]
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: Optional[str]
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    recurrence: Optional[str] = None
    reminders_minutes_before: Optional[List[int]] = None
    company_id: Optional[int] = None  # Если указано, событие корпоративное


class EventOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    recurrence: Optional[str]
    company_id: Optional[int] = None

    class Config:
        from_attributes = True


class ReminderOut(BaseModel):
    id: int
    remind_at: datetime
    sent: bool

    class Config:
        from_attributes = True


class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CompanyOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyMemberCreate(BaseModel):
    user_email: str  # Email пользователя для добавления в компанию


class CompanyMemberOut(BaseModel):
    id: int
    company_id: int
    user_id: int
    role: str
    joined_at: datetime
    user: UserOut

    class Config:
        from_attributes = True


