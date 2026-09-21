import uuid
from sqlalchemy import String, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
import enum

class ConversationMode(str, enum.Enum):
    CHAT = "CHAT"
    RESEARCH = "RESEARCH"
    BUILD = "BUILD"
    AGENT = "AGENT"
    ANALYZE = "ANALYZE"
    IMAGE = "IMAGE"

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    title: Mapped[str] = mapped_column(String)
    mode: Mapped[ConversationMode] = mapped_column(SQLEnum(ConversationMode))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
