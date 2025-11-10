from datetime import timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .db import get_db
from .models import Event, Reminder, User
from .schemas import EventCreate, EventOut, ReminderOut, UserOut
from .auth import get_current_user


router = APIRouter(prefix="/events", tags=["events"])

def _to_naive_utc(dt):
    """Привести datetime к naive (UTC без tzinfo)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # в UTC и убираем tzinfo
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.post("/", response_model=EventOut)
async def create_event(payload: EventCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Проверяем, что если указана компания, пользователь является её участником
    if payload.company_id:
        from .models import CompanyMember
        result = await db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == payload.company_id,
                CompanyMember.user_id == user.id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=403, detail="Вы не являетесь участником этой компании")
    
    start = _to_naive_utc(payload.start_time)
    event = Event(
        user_id=user.id,
        company_id=payload.company_id,
        title=payload.title,
        description=payload.description,
        start_time=start,
        recurrence=payload.recurrence,
    )
    db.add(event)
    await db.flush()

    # reminders_minutes_before: create Reminder records
    reminder_offsets = set(payload.reminders_minutes_before or [])
    reminder_offsets.add(0)
    for minutes in sorted(reminder_offsets):
        if minutes < 0:
            continue
        remind_at = start - timedelta(minutes=minutes)
        db.add(Reminder(event_id=event.id, remind_at=remind_at))

    await db.commit()
    await db.refresh(event)
    return event


@router.get("/", response_model=list[EventOut])
async def list_events(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Получаем события пользователя и корпоративные события компаний, в которых он состоит
    from .models import CompanyMember
    # Получаем ID компаний пользователя
    company_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user.id)
    )
    company_ids = [row[0] for row in company_result.all()]
    
    # События пользователя или корпоративные события его компаний
    if company_ids:
        query = select(Event).where(
            (Event.user_id == user.id) | (Event.company_id.in_(company_ids))
        ).order_by(Event.start_time)
    else:
        query = select(Event).where(Event.user_id == user.id).order_by(Event.start_time)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Проверяем личные события и корпоративные события компаний пользователя
    from .models import CompanyMember
    company_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user.id)
    )
    company_ids = [row[0] for row in company_result.all()]
    
    if company_ids:
        result = await db.execute(
            select(Event).where(
                Event.id == event_id,
                ((Event.user_id == user.id) | (Event.company_id.in_(company_ids)))
            )
        )
    else:
        result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Проверяем личные события и корпоративные события компаний пользователя
    from .models import CompanyMember
    company_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user.id)
    )
    company_ids = [row[0] for row in company_result.all()]
    
    if company_ids:
        result = await db.execute(
            select(Event).where(
                Event.id == event_id,
                ((Event.user_id == user.id) | (Event.company_id.in_(company_ids)))
            )
        )
    else:
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
    # Проверяем личные события и корпоративные события компаний пользователя
    from .models import CompanyMember
    company_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user.id)
    )
    company_ids = [row[0] for row in company_result.all()]
    
    if company_ids:
        result = await db.execute(
            select(Event).where(
                Event.id == event_id,
                ((Event.user_id == user.id) | (Event.company_id.in_(company_ids)))
            )
        )
    else:
        result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    start = _to_naive_utc(payload.start_time)

    # Проверяем права на изменение корпоративного события
    if payload.company_id:
        from .models import CompanyMember
        result = await db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == payload.company_id,
                CompanyMember.user_id == user.id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=403, detail="Вы не являетесь участником этой компании")
    
    # Обновляем поля события
    event.title = payload.title
    event.description = payload.description
    event.start_time = start
    event.recurrence = payload.recurrence
    event.company_id = payload.company_id
    
    # Удаляем старые напоминания
    await db.execute(delete(Reminder).where(Reminder.event_id == event.id))
    
    # Создаем новые напоминания
    reminder_offsets = set(payload.reminders_minutes_before or [])
    reminder_offsets.add(0)
    for minutes in sorted(reminder_offsets):
        if minutes < 0:
            continue
        remind_at = start - timedelta(minutes=minutes)
        db.add(Reminder(event_id=event.id, remind_at=remind_at))
    
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/{event_id}/reminders", response_model=list[ReminderOut])
async def list_reminders(event_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Проверяем личные события и корпоративные события компаний пользователя
    from .models import CompanyMember
    company_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user.id)
    )
    company_ids = [row[0] for row in company_result.all()]
    
    if company_ids:
        result = await db.execute(
            select(Event).where(
                Event.id == event_id,
                ((Event.user_id == user.id) | (Event.company_id.in_(company_ids)))
            )
        )
    else:
        result = await db.execute(select(Event).where(Event.id == event_id, Event.user_id == user.id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    result_r = await db.execute(select(Reminder).where(Reminder.event_id == event.id).order_by(Reminder.remind_at))
    return result_r.scalars().all()


