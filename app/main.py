from fastapi import FastAPI
from .db import engine, Base
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_telegram import router as telegram_router
from .services_scheduler import start_scheduler

# FastAPI app
app = FastAPI(title="Calendar Reminder API")

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    # Create tables if not exist (for dev). In prod use Alembic.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    start_scheduler()


app.include_router(auth_router)
app.include_router(events_router)
app.include_router(telegram_router)


