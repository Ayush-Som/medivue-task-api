from datetime import datetime, date
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    priority = Column(Integer, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)

    completed = Column(Boolean, nullable=False, default=False, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    tags = relationship("Tag", secondary=task_tags, back_populates="tasks", lazy="selectin")


Index("ix_tasks_filtering", Task.priority, Task.completed, Task.is_deleted)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)

    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

    __table_args__ = (
        UniqueConstraint("name", name="uq_tags_name"),
        Index("ix_tags_name", "name"),
    )
