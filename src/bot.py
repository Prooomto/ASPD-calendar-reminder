import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import json
import os

TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
DATA_FILE = "src/storage.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

def load_events():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_events(events):
    with open(DATA_FILE, "w") as f:
        json.dump(events, f, indent=4)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("👋 Welcome! Use /addevent YYYY-MM-DD HH:MM Your event to add reminder.")

@dp.message(Command("addevent"))
async def add_event(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❗ Format: /addevent YYYY-MM-DD HH:MM Event text")
        return
    date_str, time_str, text = parts
    try:
        event_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("❗ Wrong date format! Use YYYY-MM-DD HH:MM")
        return

    events = load_events()
    user_id = str(message.from_user.id)
    if user_id not in events:
        events[user_id] = []
    events[user_id].append({"time": event_time.isoformat(), "text": text})
    save_events(events)

    scheduler.add_job(send_reminder, 'date', run_date=event_time, args=[user_id, text])
    await message.answer(f"✅ Event added for {event_time.strftime('%Y-%m-%d %H:%M')}")

async def send_reminder(user_id, text):
    try:
        await bot.send_message(user_id, f"🔔 Reminder: {text}")
    except Exception as e:
        print("Error sending reminder:", e)

@dp.message(Command("myevents"))
async def list_events(message: types.Message):
    events = load_events()
    user_id = str(message.from_user.id)
    if user_id not in events or not events[user_id]:
        await message.answer("📭 No events yet.")
        return
    reply = "\n".join([f"- {e['time']} → {e['text']}" for e in events[user_id]])
    await message.answer(f"🗓️ Your events:\n{reply}")

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
