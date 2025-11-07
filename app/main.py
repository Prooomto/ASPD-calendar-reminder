from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_telegram import router as telegram_router
from .services_scheduler import start_scheduler

# FastAPI app
app = FastAPI(title="Calendar Reminder API")

# Разрешаем оба источника: localhost и 127.0.0.1 (и 5174 на всякий)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,     # куки/авторизация
    allow_methods=["*"],        # GET/POST/PUT/DELETE/OPTIONS
    allow_headers=["*"],        # любые заголовки (в т.ч. Content-Type, Authorization)
)

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


