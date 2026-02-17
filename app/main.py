from datetime import date
from typing import Optional, List

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, get_db
from app.models import Base
from app.schemas import TaskCreate, TaskPatch, TaskOut, PaginatedTasks
from app import crud
from app.errors import (
    request_validation_exception_handler,
    http_exception_handler,
    validation_error,
)

app = FastAPI(title="MediVue Task Management API", version="1.0.0")

app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)


@app.on_event("startup")
async def on_startup():
    # For the assessment: auto-create tables.
    # In production: use Alembic migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def ensure_due_date_not_past(d: date):
    if d < date.today():
        raise validation_error({"due_date": "Must not be in the past"})


@app.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    ensure_due_date_not_past(payload.due_date)
    task = await crud.create_task(
        db=db,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        tag_names=payload.tags,
    )
    return task


@app.get("/tasks", response_model=PaginatedTasks)
async def get_tasks(
    completed: Optional[bool] = Query(None),
    priority: Optional[int] = Query(None, ge=1, le=5),
    tags: Optional[str] = Query(None, description="CSV list, matches tasks with ANY tag"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    tags_any: Optional[List[str]] = None
    if tags:
        tags_any = [t.strip().lower() for t in tags.split(",") if t.strip()]

    total, items = await crud.list_tasks(
        db=db,
        completed=completed,
        priority=priority,
        tags_any=tags_any,
        limit=limit,
        offset=offset,
    )
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@app.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskOut)
async def patch_task(task_id: int, payload: TaskPatch, db: AsyncSession = Depends(get_db)):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.due_date is not None:
        ensure_due_date_not_past(payload.due_date)

    # detect whether description was included in request
    description_provided = "description" in payload.model_fields_set

    task = await crud.patch_task(
        db=db,
        task=task,
        title=payload.title,
        description_provided=description_provided,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        completed=payload.completed,
        tag_names=payload.tags,
    )
    return task


@app.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await crud.soft_delete_task(db, task)
    return None

@app.get("/")
async def root():
    return {"status": "ok", "message": "MediVue Task API running. Visit /docs"}
