import os
import textwrap

BASE_DIR = r"c:\Users\hp\Desktop\DAI\backend"

files = {
    "app/__init__.py": "",
    "main.py": """\
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
""",
    "app/main.py": """\
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.database import engine
from app.core.redis import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()
    await engine.dispose()

app = FastAPI(title="DAI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
""",
    "app/schemas/__init__.py": "",
    "app/schemas/auth.py": """\
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
""",
    "app/schemas/chat.py": """\
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Any

class ConversationCreate(BaseModel):
    title: str
    mode: str

class ConversationResponse(BaseModel):
    id: UUID
    title: str
    mode: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    content: str
    mode: str | None = None

class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    mode: str | None = None
    metadata_: dict[str, Any] | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConversationWithMessages(ConversationResponse):
    messages: list[MessageResponse]
""",
    "app/schemas/common.py": """\
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

class ErrorResponse(BaseModel):
    detail: str

class StatusResponse(BaseModel):
    status: str
""",
    "app/schemas/settings.py": """\
from pydantic import BaseModel, ConfigDict
from typing import Any

class SettingsUpdate(BaseModel):
    ai_provider: str | None = None
    ai_model: str | None = None
    theme: str | None = None
    preferences: dict[str, Any] | None = None

class SettingsResponse(BaseModel):
    ai_provider: str
    ai_model: str
    theme: str
    preferences: dict[str, Any] | None = None
    model_config = ConfigDict(from_attributes=True)
""",
    "app/schemas/activity.py": """\
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ActivityResponse(BaseModel):
    id: UUID
    type: str
    title: str
    description: str | None = None
    project_id: UUID | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
""",
    "app/services/__init__.py": "",
    "app/services/auth_service.py": """\
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash, verify_password
from uuid import UUID
from fastapi import HTTPException

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
""",
    "app/services/chat_service.py": """\
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ConversationCreate, MessageCreate
from app.ai.registry import get_ai_provider
from app.ai.types import ChatMessage as AIChatMessage
from uuid import UUID
import json

async def create_conversation(db: AsyncSession, user_id: UUID, conv_in: ConversationCreate) -> Conversation:
    conv = Conversation(user_id=user_id, title=conv_in.title, mode=conv_in.mode)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv

async def get_conversations(db: AsyncSession, user_id: UUID) -> list[Conversation]:
    result = await db.execute(select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()))
    return list(result.scalars().all())

async def get_conversation(db: AsyncSession, user_id: UUID, conv_id: UUID) -> Conversation | None:
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user_id))
    return result.scalars().first()

async def delete_conversation(db: AsyncSession, user_id: UUID, conv_id: UUID) -> bool:
    conv = await get_conversation(db, user_id, conv_id)
    if not conv:
        return False
    await db.delete(conv)
    await db.commit()
    return True

async def create_message(db: AsyncSession, conv_id: UUID, role: str, content: str, mode: str | None = None) -> Message:
    msg = Message(conversation_id=conv_id, role=role, content=content, mode=mode)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def get_messages(db: AsyncSession, conv_id: UUID) -> list[Message]:
    result = await db.execute(select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at.asc()))
    return list(result.scalars().all())

async def send_message_and_stream(db: AsyncSession, conv: Conversation, message_in: MessageCreate, provider_name: str = "openai"):
    # Save user message
    user_msg = await create_message(db, conv.id, "USER", message_in.content, message_in.mode)
    
    # Get history
    history = await get_messages(db, conv.id)
    ai_messages = [AIChatMessage(role=m.role.lower(), content=m.content) for m in history]
    
    provider = get_ai_provider(provider_name)
    
    async def stream_generator():
        yield f"data: {json.dumps({'event': 'message_start'})}\\n\\n"
        
        full_content = ""
        async for chunk in provider.chat_stream(ai_messages):
            if chunk.content:
                full_content += chunk.content
                yield f"data: {json.dumps({'event': 'content_delta', 'content': chunk.content})}\\n\\n"
        
        # Save assistant message
        await create_message(db, conv.id, "ASSISTANT", full_content, message_in.mode)
        
        yield f"data: {json.dumps({'event': 'message_end'})}\\n\\n"
    
    return stream_generator()
""",
    "app/services/activity_service.py": """\
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.activity import Activity
from uuid import UUID
from typing import Any

async def log_activity(db: AsyncSession, user_id: UUID, act_type: str, title: str, description: str | None = None, project_id: UUID | None = None, metadata_: dict[str, Any] | None = None) -> Activity:
    act = Activity(
        user_id=user_id,
        type=act_type,
        title=title,
        description=description,
        project_id=project_id,
        metadata_=metadata_
    )
    db.add(act)
    await db.commit()
    await db.refresh(act)
    return act

async def get_activities(db: AsyncSession, user_id: UUID, limit: int = 50) -> list[Activity]:
    result = await db.execute(select(Activity).where(Activity.user_id == user_id).order_by(Activity.created_at.desc()).limit(limit))
    return list(result.scalars().all())
""",
    "app/ai/__init__.py": "",
    "app/ai/types.py": """\
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    content: str
    model: str
    usage: dict[str, int] | None = None

class ModelInfo(BaseModel):
    id: str
    name: str
    context_window: int

class StreamChunk(BaseModel):
    content: str
    done: bool
""",
    "app/ai/base.py": """\
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from .types import ChatMessage, ChatResponse, ModelInfo

class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: list[ChatMessage], **kwargs) -> AsyncGenerator[any, None]:
        pass
    
    @abstractmethod
    async def get_models(self) -> list[ModelInfo]:
        pass
    
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def supports_tools(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        pass
""",
    "app/ai/openai_provider.py": """\
import httpx
import json
from .base import AIProvider
from .types import ChatMessage, ChatResponse, ModelInfo, StreamChunk
from app.config import settings

class OpenAIProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": kwargs.get("model", "gpt-4o"),
                "messages": [m.model_dump() for m in messages],
                "stream": False
            }
            resp = await client.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            return ChatResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data.get("usage")
            )

    async def chat_stream(self, messages: list[ChatMessage], **kwargs):
        async with httpx.AsyncClient() as client:
            payload = {
                "model": kwargs.get("model", "gpt-4o"),
                "messages": [m.model_dump() for m in messages],
                "stream": True
            }
            async with client.stream("POST", f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=60.0) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:]
                        if line == "[DONE]":
                            yield StreamChunk(content="", done=True)
                            break
                        try:
                            data = json.loads(line)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            yield StreamChunk(content=content, done=False)
                        except json.JSONDecodeError:
                            continue

    async def get_models(self) -> list[ModelInfo]:
        return [ModelInfo(id="gpt-4o", name="GPT-4o", context_window=128000)]

    @property
    def supports_streaming(self) -> bool: return True
    @property
    def supports_tools(self) -> bool: return True
    @property
    def supports_vision(self) -> bool: return True
""",
    "app/ai/anthropic_provider.py": """\
from .base import AIProvider
class AnthropicProvider(AIProvider):
    async def chat(self, messages, **kwargs): raise NotImplementedError
    async def chat_stream(self, messages, **kwargs): raise NotImplementedError
    async def get_models(self): raise NotImplementedError
    @property
    def supports_streaming(self) -> bool: return False
    @property
    def supports_tools(self) -> bool: return False
    @property
    def supports_vision(self) -> bool: return False
""",
    "app/ai/google_provider.py": """\
from .base import AIProvider
class GoogleProvider(AIProvider):
    async def chat(self, messages, **kwargs): raise NotImplementedError
    async def chat_stream(self, messages, **kwargs): raise NotImplementedError
    async def get_models(self): raise NotImplementedError
    @property
    def supports_streaming(self) -> bool: return False
    @property
    def supports_tools(self) -> bool: return False
    @property
    def supports_vision(self) -> bool: return False
""",
    "app/ai/registry.py": """\
from .base import AIProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider

_providers = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider
}

def get_ai_provider(provider_name: str = "openai") -> AIProvider:
    provider_cls = _providers.get(provider_name.lower())
    if not provider_cls:
        raise ValueError(f"Provider {provider_name} not found")
    return provider_cls()
""",
    "app/api/__init__.py": "",
    "app/api/deps.py": """\
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from uuid import UUID

from app.core.database import get_db
from app.core.security import ALGORITHM
from app.config import settings
from app.models.user import User
from app.services.auth_service import get_user_by_id
from app.ai.registry import get_ai_provider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except JWTError:
        raise credentials_exception
        
    user = await get_user_by_id(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user
""",
    "app/api/v1/__init__.py": "",
    "app/api/v1/router.py": """\
from fastapi import APIRouter
from .endpoints import auth, chat, settings, activities, health

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(health.router, tags=["health"])
""",
    "app/api/v1/endpoints/__init__.py": "",
    "app/api/v1/endpoints/auth.py": """\
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.auth import UserCreate, UserResponse, Token
from app.services.auth_service import register_user, authenticate_user
from app.core.security import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await register_user(db, user_in)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return {"access_token": access_token, "refresh_token": access_token, "token_type": "bearer"}
""",
    "app/api/v1/endpoints/chat.py": """\
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.chat import ConversationCreate, ConversationResponse, MessageCreate, ConversationWithMessages, MessageResponse
from app.services.chat_service import create_conversation, get_conversations, get_conversation, delete_conversation, send_message_and_stream, get_messages
from app.models.user import User
from starlette.responses import StreamingResponse
from uuid import UUID

router = APIRouter()

@router.post("/conversations", response_model=ConversationResponse)
async def create_conv(conv_in: ConversationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await create_conversation(db, current_user.id, conv_in)

@router.get("/conversations", response_model=list[ConversationResponse])
async def list_convs(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await get_conversations(db, current_user.id)

@router.get("/conversations/{conv_id}", response_model=ConversationWithMessages)
async def get_conv(conv_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = await get_conversation(db, current_user.id, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await get_messages(db, conv_id)
    conv_resp = ConversationWithMessages.model_validate(conv, update={"messages": [MessageResponse.model_validate(m) for m in messages]})
    return conv_resp

@router.delete("/conversations/{conv_id}")
async def delete_conv(conv_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = await delete_conversation(db, current_user.id, conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}

@router.post("/conversations/{conv_id}/messages")
async def send_message(conv_id: UUID, message_in: MessageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    conv = await get_conversation(db, current_user.id, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    stream = await send_message_and_stream(db, conv, message_in)
    return StreamingResponse(stream, media_type="text/event-stream")
""",
    "app/api/v1/endpoints/settings.py": """\
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
""",
    "app/api/v1/endpoints/activities.py": """\
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.services.activity_service import get_activities

router = APIRouter()

@router.get("/", response_model=list[ActivityResponse])
async def list_activities(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await get_activities(db, current_user.id)
""",
    "app/api/v1/endpoints/health.py": """\
from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
async def health():
    return {"status": "ok"}
""",
    "app/middleware/__init__.py": "",
    "app/middleware/rate_limit.py": """\
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Stub for rate limit
        response = await call_next(request)
        return response
""",
    "alembic.ini": """\
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""",
    "alembic/env.py": """\
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.config import settings
from app.models.base import Base
# Import all models to ensure they are registered
import app.models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""",
    "alembic/script.py.mako": """\
\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
""",
    "alembic/versions/.gitkeep": "",
    "tests/__init__.py": "",
    "tests/conftest.py": """\
import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import get_db, Base
from app.core.security import create_access_token
from app.models.user import User
import uuid

# Use a test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def test_user(db_session):
    from app.core.security import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
def auth_token(test_user):
    return create_access_token(data={"sub": str(test_user.id)})
""",
    "tests/test_auth.py": """\
import pytest

@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "pass",
        "full_name": "New User"
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@example.com"

@pytest.mark.asyncio
async def test_login(client, test_user):
    resp = await client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "password123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_me(client, auth_token):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"
""",
    "tests/test_chat.py": """\
import pytest
from app.models.conversation import Conversation
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_conversation(client, auth_token):
    resp = await client.post("/api/v1/chat/conversations", headers={"Authorization": f"Bearer {auth_token}"}, json={
        "title": "Test Chat",
        "mode": "CHAT"
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Chat"

@pytest.mark.asyncio
async def test_list_conversations(client, auth_token, db_session, test_user):
    conv = Conversation(user_id=test_user.id, title="Test List", mode="CHAT")
    db_session.add(conv)
    await db_session.commit()

    resp = await client.get("/api/v1/chat/conversations", headers={"Authorization": f"Bearer {auth_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
"""
}

for rel_path, content in files.items():
    full_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Generated {len(files)} files successfully.")
