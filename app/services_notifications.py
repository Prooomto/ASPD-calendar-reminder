import os
import httpx


BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def send_telegram_message(chat_id: str, text: str) -> bool:
    if not BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": text})
        return resp.status_code == 200 and resp.json().get("ok", False)


