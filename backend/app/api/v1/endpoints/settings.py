from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.setting import Setting
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter()

@router.get("/", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Setting).where(Setting.user_id == current_user.id))
    setting = result.scalars().first()
    if not setting:
        setting = Setting(user_id=current_user.id)
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
    return setting

@router.put("/", response_model=SettingsResponse)
async def update_settings(settings_in: SettingsUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Setting).where(Setting.user_id == current_user.id))
    setting = result.scalars().first()
    if not setting:
        setting = Setting(user_id=current_user.id)
        db.add(setting)
    
    if settings_in.ai_provider is not None: setting.ai_provider = settings_in.ai_provider
    if settings_in.ai_model is not None: setting.ai_model = settings_in.ai_model
    if settings_in.theme is not None: setting.theme = settings_in.theme
    if settings_in.preferences is not None: setting.preferences = settings_in.preferences
    
    await db.commit()
    await db.refresh(setting)
    return setting
