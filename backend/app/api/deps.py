import uuid
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.database import get_db
from app.core.security import ALGORITHM
from app.config import settings
from app.models.user import User
from app.services.auth_service import get_user_by_id, get_user_by_email
from app.ai.registry import get_ai_provider as _get_ai_provider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token:
        # 1. Try local JWT verification
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id_str: str | None = payload.get("sub")
            if user_id_str:
                user_id = uuid.UUID(user_id_str)
                user = await get_user_by_id(db, user_id=user_id)
                if user:
                    return user
        except Exception:
            pass

        # 2. Try Clerk JWT decoding & mapping
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id_str: str | None = payload.get("sub")
            email: str | None = payload.get("email") or payload.get("email_address")
            if email:
                user = await get_user_by_email(db, email)
                if user:
                    return user
            if user_id_str:
                deterministic_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id_str)
                user = await get_user_by_id(db, user_id=deterministic_uuid)
                if user:
                    return user
                # Auto-create Clerk user record
                new_user = User(
                    id=deterministic_uuid,
                    email=email or f"{user_id_str}@clerk.local",
                    hashed_password="",
                    full_name=payload.get("name") or "DAI User"
                )
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                return new_user
        except Exception:
            pass

    # 3. Development Fallback: Primary active database user
    result = await db.execute(select(User).where(User.is_active == True).order_by(User.id))
    default_user = result.scalars().first()
    if default_user:
        return default_user

    raise credentials_exception


def get_provider():
    """Dependency that returns the configured AI provider."""
    return _get_ai_provider()
