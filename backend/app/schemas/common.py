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
