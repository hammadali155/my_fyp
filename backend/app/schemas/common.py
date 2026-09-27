from __future__ import annotations

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class PaginatedParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    page: int
    page_size: int
    total: int
