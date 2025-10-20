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


class EventOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    recurrence: Optional[str]

    class Config:
        from_attributes = True


class ReminderOut(BaseModel):
    id: int
    remind_at: datetime
    sent: bool

    class Config:
        from_attributes = True


