import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .db import get_db
from .models import TelegramLink, User
from .auth import get_current_user


router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/link/start")
async def start_link(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    code = secrets.token_hex(4)
    link = TelegramLink(user_id=user.id, code=code, confirmed=False)
    db.add(link)
    await db.commit()
    return {"code": code, "message": "Отправьте этот код боту командой /link <code>"}


@router.post("/link/confirm")
async def confirm_link(telegram_id: str, code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TelegramLink, User).join(User, TelegramLink.user_id == User.id).where(TelegramLink.code == code))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Код не найден")
    link, user = row
    await db.execute(update(User).where(User.id == user.id).values(telegram_id=telegram_id))
    await db.execute(update(TelegramLink).where(TelegramLink.id == link.id).values(confirmed=True))
    await db.commit()
    return {"status": "linked"}


