import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .db import get_db
from .models import TelegramLink, User
from .auth import get_current_user
from .auth import create_access_token


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
    # сразу выдаем JWT для удобства бота
    token = create_access_token(subject=user.email)
    return {"status": "linked", "access_token": token, "token_type": "bearer"}

@router.post("/token")
async def get_token_by_telegram(telegram_id: str, db: AsyncSession = Depends(get_db)):
    # Находим пользователя по telegram_id и выдаем ему JWT
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь с таким telegram_id не найден или не связан")
    token = create_access_token(subject=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/link/status")
async def link_status(user: User = Depends(get_current_user)):
    return {"linked": bool(user.telegram_id), "telegram_id": user.telegram_id}
