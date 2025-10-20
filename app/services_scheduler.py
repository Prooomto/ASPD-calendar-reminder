from datetime import datetime
from typing import Callable, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler


scheduler = AsyncIOScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def schedule_job(func: Callable[..., Any], run_at: datetime, args: list[Any] | None = None):
    scheduler.add_job(func, 'date', run_date=run_at, args=args or [])


