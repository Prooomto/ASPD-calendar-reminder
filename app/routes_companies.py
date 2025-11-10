from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from .db import get_db
from .models import Company, CompanyMember, User
from .schemas import CompanyCreate, CompanyOut, CompanyMemberCreate, CompanyMemberOut, UserOut
from .auth import get_current_user

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("/", response_model=CompanyOut)
async def create_company(
    payload: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Создать новую компанию"""
    company = Company(
        name=payload.name,
        description=payload.description,
        created_by=user.id
    )
    db.add(company)
    await db.flush()
    
    # Автоматически добавляем создателя как владельца компании
    member = CompanyMember(
        company_id=company.id,
        user_id=user.id,
        role="owner"
    )
    db.add(member)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("/", response_model=list[CompanyOut])
async def list_my_companies(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Получить список компаний, в которых состоит пользователь"""
    result = await db.execute(
        select(Company)
        .join(CompanyMember, Company.id == CompanyMember.company_id)
        .where(CompanyMember.user_id == user.id)
        .order_by(Company.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Получить информацию о компании"""
    # Проверяем, что пользователь является участником компании
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Вы не являетесь участником этой компании")
    
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return company


@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Удалить компанию (только владелец)"""
    # Проверяем, что пользователь является владельцем
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.id,
            CompanyMember.role == "owner"
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Только владелец может удалить компанию")
    
    await db.execute(delete(Company).where(Company.id == company_id))
    await db.commit()
    return {"status": "deleted"}


@router.post("/{company_id}/members", response_model=CompanyMemberOut)
async def add_member(
    company_id: int,
    payload: CompanyMemberCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Добавить участника в компанию (только владелец или админ)"""
    # Проверяем права
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.id
        )
    )
    member = result.scalar_one_or_none()
    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Только владелец или админ могут добавлять участников")
    
    # Находим пользователя по email
    result = await db.execute(select(User).where(User.email == payload.user_email))
    new_user = result.scalar_one_or_none()
    if not new_user:
        raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")
    
    # Проверяем, не является ли уже участником
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == new_user.id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже является участником компании")
    
    # Добавляем участника
    new_member = CompanyMember(
        company_id=company_id,
        user_id=new_user.id,
        role="member"
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    
    # Загружаем связанного пользователя для ответа
    await db.refresh(new_member, ["user"])
    return new_member


@router.get("/{company_id}/members", response_model=list[CompanyMemberOut])
async def list_members(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Получить список участников компании"""
    # Проверяем, что пользователь является участником компании
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Вы не являетесь участником этой компании")
    
    result = await db.execute(
        select(CompanyMember)
        .where(CompanyMember.company_id == company_id)
        .order_by(CompanyMember.joined_at)
    )
    members = result.scalars().all()
    
    # Загружаем связанных пользователей
    for m in members:
        await db.refresh(m, ["user"])
    
    return members


@router.delete("/{company_id}/members/{member_id}")
async def remove_member(
    company_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Удалить участника из компании (только владелец или админ, или сам участник)"""
    # Проверяем права текущего пользователя
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.id
        )
    )
    current_member = result.scalar_one_or_none()
    if not current_member:
        raise HTTPException(status_code=403, detail="Вы не являетесь участником этой компании")
    
    # Получаем участника для удаления
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.id == member_id,
            CompanyMember.company_id == company_id
        )
    )
    target_member = result.scalar_one_or_none()
    if not target_member:
        raise HTTPException(status_code=404, detail="Участник не найден")
    
    # Проверяем права: владелец/админ может удалить любого, кроме владельца
    # Обычный участник может удалить только себя
    if current_member.role not in ["owner", "admin"]:
        if target_member.user_id != user.id:
            raise HTTPException(status_code=403, detail="Вы можете удалить только себя")
    
    # Владелец не может быть удален
    if target_member.role == "owner":
        raise HTTPException(status_code=403, detail="Владелец не может быть удален")
    
    await db.execute(delete(CompanyMember).where(CompanyMember.id == member_id))
    await db.commit()
    return {"status": "removed"}


@router.put("/{company_id}/members/{member_id}/role")
async def update_member_role(
    company_id: int,
    member_id: int,
    role: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Изменить роль участника (только владелец)"""
    if role not in ["owner", "admin", "member"]:
        raise HTTPException(status_code=400, detail="Недопустимая роль")
    
    # Проверяем, что текущий пользователь - владелец
    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user.id,
            CompanyMember.role == "owner"
        )
    )
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=403, detail="Только владелец может изменять роли")
    
    # Обновляем роль
    await db.execute(
        update(CompanyMember)
        .where(CompanyMember.id == member_id, CompanyMember.company_id == company_id)
        .values(role=role)
    )
    await db.commit()
    return {"status": "updated"}

