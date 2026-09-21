import uuid
from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
import enum

class ProjectStatus(str, enum.Enum):
    IDEA = "IDEA"
    PLANNING = "PLANNING"
    BUILDING = "BUILDING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(SQLEnum(ProjectStatus))
    tech_stack: Mapped[dict | None] = mapped_column(JSON, nullable=True)
