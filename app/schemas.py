from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: int = Field(..., ge=1, le=5)
    due_date: date
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v):
        if v is None:
            return v
        cleaned = []
        for t in v:
            if t is None:
                continue
            s = t.strip().lower()
            if s:
                cleaned.append(s)
        # de-dupe while preserving order
        seen = set()
        out = []
        for t in cleaned:
            if t not in seen:
                out.append(t)
                seen.add(t)
        return out


class TaskPatch(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v):
        if v is None:
            return v
        cleaned = []
        for t in v:
            if t is None:
                continue
            s = t.strip().lower()
            if s:
                cleaned.append(s)
        seen = set()
        out = []
        for t in cleaned:
            if t not in seen:
                out.append(t)
                seen.add(t)
        return out


class TagOut(BaseModel):
    name: str

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: int
    due_date: date
    completed: bool
    tags: List[TagOut]

    class Config:
        from_attributes = True


class PaginatedTasks(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[TaskOut]
