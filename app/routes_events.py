from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .db import get_db
from .models import Event, Reminder, User
from .schemas import EventCreate, EventOut, ReminderOut
from .auth import get_current_user


router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventOut)
async def create_event(payload: EventCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    event = Event(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        start_time=payload.start_time,
        recurrence=payload.recurrence,
    )
    db.add(event)
    await db.flush()

    # reminders_minutes_before: create Reminder records
    if payload.reminders_minutes_before:
        for minutes in payload.reminders_minutes_before:
            remind_at = payload.start_time - timedelta(minutes=minutes)
            db.add(Reminder(event_id=event.id, remind_at=remind_at))

    await db.commit()
    await db.refresh(event)
    return event


@router.get("/", response_model=list[EventOut])
async def list_events(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Event).where(Event.user_id == user.id).order_by(Event.start_time))
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.execute(delete(Reminder).where(Reminder.event_id == event.id))
    await db.execute(delete(Event).where(Event.id == event.id))
    await db.commit()
    return {"status": "deleted"}


@router.put("/{event_id}", response_model=EventOut)
async def update_event(event_id: int, payload: EventCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Обновляем поля события
    event.title = payload.title
    event.description = payload.description
    event.start_time = payload.start_time
    event.recurrence = payload.recurrence
    
    # Удаляем старые напоминания
    await db.execute(delete(Reminder).where(Reminder.event_id == event.id))
    
    # Создаем новые напоминания
    if payload.reminders_minutes_before:
        for minutes in payload.reminders_minutes_before:
            remind_at = payload.start_time - timedelta(minutes=minutes)
            db.add(Reminder(event_id=event.id, remind_at=remind_at))
    
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/{event_id}/reminders", response_model=list[ReminderOut])
async def list_reminders(event_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    result_r = await db.execute(select(Reminder).where(Reminder.event_id == event.id).order_by(Reminder.remind_at))
    return result_r.scalars().all()


