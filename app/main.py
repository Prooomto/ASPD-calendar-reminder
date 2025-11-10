from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base
from .routes_auth import router as auth_router
from .routes_events import router as events_router
from .routes_telegram import router as telegram_router
from .routes_companies import router as companies_router
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
        # lightweight auto-migration to ensure corporate column exists on events
        # 1) add company_id column if missing
        await conn.exec_driver_sql(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'events' AND column_name = 'company_id'
                ) THEN
                    ALTER TABLE events ADD COLUMN company_id INTEGER;
                END IF;
            END
            $$;
            """
        )
        # 2) add index for company_id if missing
        await conn.exec_driver_sql(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = 'ix_events_company_id' AND n.nspname = 'public'
                ) THEN
                    CREATE INDEX ix_events_company_id ON events (company_id);
                END IF;
            END
            $$;
            """
        )
        # 3) add foreign key to companies if missing
        await conn.exec_driver_sql(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = 'fk_events_company_id_companies_id'
                ) THEN
                    ALTER TABLE events
                    ADD CONSTRAINT fk_events_company_id_companies_id
                    FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE;
                END IF;
            END
            $$;
            """
        )
    start_scheduler()


app.include_router(auth_router)
app.include_router(events_router)
app.include_router(telegram_router)
app.include_router(companies_router)


