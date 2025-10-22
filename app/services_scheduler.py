from datetime import datetime
from typing import Callable, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .db import AsyncSessionLocal
from .services_reminders import process_due_reminders


scheduler = AsyncIOScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        # Добавляем периодическую задачу для обработки напоминаний каждую минуту
        scheduler.add_job(
            check_reminders,
            trigger=IntervalTrigger(minutes=1),
            id='check_reminders',
            replace_existing=True
        )


async def check_reminders():
    """Периодическая задача для проверки и отправки напоминаний"""
    async with AsyncSessionLocal() as db:
        await process_due_reminders(db)


def schedule_job(func: Callable[..., Any], run_at: datetime, args: list[Any] | None = None):
    scheduler.add_job(func, 'date', run_date=run_at, args=args or [])


