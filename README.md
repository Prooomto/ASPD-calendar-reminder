# Calendar Reminder Bot

A simple Telegram bot for creating and receiving event reminders.

## Features
- `/addevent YYYY-MM-DD HH:MM Text` — add event
- `/myevents` — view your events
- Auto-reminders via APScheduler
- CI/CD with GitHub Actions

## Tech Stack
Python, FastAPI, SQLAlchemy, Alembic, Aiogram, APScheduler, Pytest, GitHub Actions

## How to run (dev)
pip install -r requirements.txt
export BOT_TOKEN=YOUR_TELEGRAM_TOKEN
export DATABASE_URL=sqlite+aiosqlite:///./app.db
uvicorn app.main:app --reload
# (optional) run the bot separately
python src/bot.py

## Run tests
pytest

## Devs
- Rash Yestebek  
- Omar Mukatay  
- Daniil Alexandrov 

CSE-2403M · Astana 2025