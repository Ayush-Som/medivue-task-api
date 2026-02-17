from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Tag, Task


async def get_or_create_tags(db: AsyncSession, names: List[str]) -> List[Tag]:
    if not names:
        return []

    # De-dup while preserving order
    seen = set()
    clean_names: List[str] = []
    for n in names:
        n = (n or "").strip()
        if n and n not in seen:
            seen.add(n)
            clean_names.append(n)

    if not clean_names:
        return []

    existing = (
        (await db.execute(select(Tag).where(Tag.name.in_(clean_names))))
        .scalars()
        .all()
    )
    existing_map = {t.name: t for t in existing}

    tags: List[Tag] = []
    for name in clean_names:
        if name in existing_map:
            tags.append(existing_map[name])
        else:
            t = Tag(name=name)
            db.add(t)
            tags.append(t)

    # flush so new tags get ids before relationship assignment
    await db.flush()
    return tags


async def create_task(
    db: AsyncSession,
    title: str,
    description: Optional[str],
    priority: int,
    due_date: date,
    tag_names: Optional[List[str]],
) -> Task:
    tags: List[Tag] = []
    if tag_names is not None:
        tags = await get_or_create_tags(db, tag_names)

    task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        completed=False,
        is_deleted=False,
        tags=tags,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: int) -> Optional[Task]:
    q = (
        select(Task)
        .where(Task.id == task_id, Task.is_deleted == False)  # noqa: E712
        .options(selectinload(Task.tags))
    )
    task = (await db.execute(q)).scalars().first()
    return task


async def list_tasks(
    db: AsyncSession,
    completed: Optional[bool],
    priority: Optional[int],
    tags_any: Optional[List[str]],
    limit: int,
    offset: int,
) -> Tuple[int, List[Task]]:
    base = select(Task).where(Task.is_deleted == False)  # noqa: E712

    if completed is not None:
        base = base.where(Task.completed == completed)
    if priority is not None:
        base = base.where(Task.priority == priority)

    if tags_any:
        clean_tags = [t.strip() for t in tags_any if t and t.strip()]
        if clean_tags:
            base = base.join(Task.tags).where(Tag.name.in_(clean_tags)).distinct()

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    items_q = (
        base.options(selectinload(Task.tags))
        .order_by(Task.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = (await db.execute(items_q)).scalars().all()
    return total, items


async def patch_task(
    db: AsyncSession,
    task: Task,
    *,
    title: Optional[str],
    description_provided: bool,
    description: Optional[str],
    priority: Optional[int],
    due_date: Optional[date],
    completed: Optional[bool],
    tag_names: Optional[List[str]],
) -> Task:
    if title is not None:
        task.title = title
    if priority is not None:
        task.priority = priority
    if due_date is not None:
        task.due_date = due_date
    if completed is not None:
        task.completed = completed

    # Only overwrite description if explicitly provided in request
    if description_provided:
        task.description = description

    # If tags field is present, replace tags (supports clearing with [])
    if tag_names is not None:
        task.tags = await get_or_create_tags(db, tag_names)

    await db.commit()
    await db.refresh(task)
    return task


async def soft_delete_task(db: AsyncSession, task: Task) -> None:
    task.is_deleted = True
    await db.commit()
