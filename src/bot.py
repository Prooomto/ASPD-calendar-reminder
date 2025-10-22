import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta    
import json
import os
import httpx
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "")
DATA_FILE = "src/storage.json"
TOKENS_FILE = "src/tokens.json"

if not TOKEN:
    print("❌ BOT_TOKEN not found in environment variables!")
    exit(1)

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

def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tokens(tokens):
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=4)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("👋 Welcome! Use /addevent YYYY-MM-DD HH:MM Your event to add reminder.\nLink account: /link <code> (get code on website)")

@dp.message(Command("addevent"))
async def add_event(message: types.Message):
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("❗ Format: /addevent YYYY-MM-DD HH:MM Event text")
        return
    date_str, time_str, text = parts[1], parts[2], parts[3]
    try:
        event_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("❗ Wrong date format! Use YYYY-MM-DD HH:MM")
        return

    # Получаем/обновляем JWT для пользователя
    user_id = str(message.from_user.id)
    tokens = load_tokens()
    token = tokens.get(user_id)
    try:
        api_url = os.getenv("API_URL", "http://localhost:8000")
        async with httpx.AsyncClient(timeout=10) as client:
            if not token:
                # Пытаемся получить токен по telegram_id
                token_resp = await client.post(f"{api_url}/telegram/token", params={"telegram_id": user_id})
                if token_resp.status_code == 200:
                    token = token_resp.json().get("access_token")
                    if token:
                        tokens[user_id] = token
                        save_tokens(tokens)
                else:
                    await message.answer("❗ Сначала привяжите аккаунт командой /link <code> на сайте")
                    return

            # Создаем событие через API с корректным JWT
            event_data = {
                "title": text,
                "description": f"Создано через Telegram бота",
                "start_time": event_time.isoformat(),
                "reminders_minutes_before": [5, 30]
            }
            create_resp = await client.post(
                f"{api_url}/events/",
                json=event_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            if create_resp.status_code == 200:
                await message.answer(f"✅ Event added for {event_time.strftime('%Y-%m-%d %H:%M')}")
            elif create_resp.status_code == 401:
                # Токен устарел — пробуем обновить по telegram_id
                token_resp = await client.post(f"{api_url}/telegram/token", params={"telegram_id": user_id})
                if token_resp.status_code == 200:
                    token = token_resp.json().get("access_token")
                    if token:
                        tokens[user_id] = token
                        save_tokens(tokens)
                        retry_resp = await client.post(
                            f"{api_url}/events/",
                            json=event_data,
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        if retry_resp.status_code == 200:
                            await message.answer(f"✅ Event added for {event_time.strftime('%Y-%m-%d %H:%M')}")
                            return
                await message.answer("❗ Не удалось создать событие. Повторите привязку /link")
            else:
                await message.answer("❗ Не удалось создать событие. Попробуйте позже.")
    except Exception as e:
        print(f"Error creating event: {e}")
        await message.answer("❗ Service unavailable. Try later.")

async def send_reminder(user_id, text):
    try:
        await bot.send_message(user_id, f"🔔 Reminder: {text}")
    except Exception as e:
        print("Error sending reminder:", e)

@dp.message(Command("myevents"))
async def list_events(message: types.Message):
    user_id = str(message.from_user.id)
    tokens = load_tokens()
    token = tokens.get(user_id)
    try:
        api_url = os.getenv("API_URL", "http://localhost:8000")
        async with httpx.AsyncClient(timeout=10) as client:
            if not token:
                token_resp = await client.post(f"{api_url}/telegram/token", params={"telegram_id": user_id})
                if token_resp.status_code == 200:
                    token = token_resp.json().get("access_token")
                    if token:
                        tokens[user_id] = token
                        save_tokens(tokens)
                else:
                    await message.answer("❗ Сначала привяжите аккаунт командой /link <code>")
                    return

            resp = await client.get(f"{api_url}/events/", headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                events = resp.json()
                if not events:
                    await message.answer("📭 No events yet.")
                    return
                reply = "\n".join([f"- {e['start_time']} → {e['title']}" for e in events])
                await message.answer(f"🗓️ Your events:\n{reply}")
            elif resp.status_code == 401:
                await message.answer("❗ Сессия истекла. Повторите привязку /link")
            else:
                await message.answer("❗ Please link your account first with /link")
    except Exception as e:
        print(f"Error getting events: {e}")
        await message.answer("❗ Service unavailable. Try later.")


@dp.message(Command("link"))
async def link_account(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❗ Use: /link <code>")
        return
    code = parts[1].strip()
    try:
        api_url = os.getenv("API_URL", "http://localhost:8000")
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{api_url}/telegram/link/confirm",
                params={"telegram_id": str(message.from_user.id), "code": code}
            )
            if resp.status_code == 200:
                data = resp.json()
                access_token = data.get("access_token")
                if access_token:
                    tokens = load_tokens()
                    tokens[str(message.from_user.id)] = access_token
                    save_tokens(tokens)
                await message.answer("✅ Account linked!")
            else:
                await message.answer("❗ Link failed. Check code on website.")
    except Exception as e:
        print(f"Error linking account: {e}")
        await message.answer("❗ Service unavailable. Try later.")

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
