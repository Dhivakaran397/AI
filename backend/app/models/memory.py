import uuid
from sqlalchemy import String, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.models.base import Base
from datetime import datetime
from sqlalchemy import DateTime
import enum

class MemoryType(str, enum.Enum):
    SHORT_TERM = "SHORT_TERM"
    PROJECT = "PROJECT"
    PREFERENCE = "PREFERENCE"
    KNOWLEDGE = "KNOWLEDGE"
    DECISION = "DECISION"

class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    type: Mapped[MemoryType] = mapped_column(SQLEnum(MemoryType))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[str | None] = mapped_column(Vector(1536), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
