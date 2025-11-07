from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import Reminder, Event, User
from .services_notifications import send_telegram_message

async def process_due_reminders(db: AsyncSession) -> int:
    # берём "сейчас" в UTC
    now_utc = datetime.now(timezone.utc)

    # забираем все неотправленные
    result = await db.execute(
        select(Reminder).where(Reminder.sent == False)  # noqa: E712
    )
    reminders = result.scalars().all()

    sent_count = 0
    for rem in reminders:
        # приводим remind_at к UTC-aware
        ra = rem.remind_at
        if ra.tzinfo is None:
            # в БД timestamp without time zone, мы туда кладём UTC — помечаем это явно
            ra_utc = ra.replace(tzinfo=timezone.utc)
        else:
            ra_utc = ra.astimezone(timezone.utc)

        # триггерим только если наступило время
        if ra_utc <= now_utc:
            event_result = await db.execute(
                select(Event, User)
                .join(User, Event.user_id == User.id)
                .where(Event.id == rem.event_id)
            )
            row = event_result.first()
            if not row:
                continue
            event, user = row
            if not user.telegram_id:
                continue

            ok = await send_telegram_message(user.telegram_id, f"🔔 Напоминание: {event.title}")
            if ok:
                await db.execute(
                    update(Reminder).where(Reminder.id == rem.id).values(sent=True)
                )
                sent_count += 1

    if sent_count:
        await db.commit()
    return sent_count

