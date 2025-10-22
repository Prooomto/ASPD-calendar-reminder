import httpx
from .config import settings


async def send_telegram_message(chat_id: str, text: str) -> bool:
    bot_token = settings.bot_token
    if not bot_token:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"chat_id": chat_id, "text": text})
        return resp.status_code == 200 and resp.json().get("ok", False)


