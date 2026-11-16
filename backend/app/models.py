"""SQLAlchemy 表定义。JSON 字段统一用 JSON 类型，SQLite / Postgres 都兼容。"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    subtitle: Mapped[str | None] = mapped_column(String(128), default=None)
    topic: Mapped[str | None] = mapped_column(String(64), default=None)
    order_no: Mapped[int] = mapped_column(Integer, default=0)
    goals_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    misc_meta: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str | None] = mapped_column(String(500), default=None)
    term: Mapped[str | None] = mapped_column(String(64), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Segment(Base):
    """内容片段。seq 为空表示它是 agent 手里的补充牌（is_hook=1）。"""

    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    chapter_id: Mapped[str] = mapped_column(String(32), ForeignKey("chapters.id"), index=True)
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(24), default="story")
    is_hook: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_checkpoint: Mapped[int] = mapped_column(Integer, default=0)
    variant: Mapped[str | None] = mapped_column(String(24), default=None)
    title: Mapped[str | None] = mapped_column(String(128), default=None)
    goal_tag: Mapped[str | None] = mapped_column(String(16), default=None)
    image: Mapped[str | None] = mapped_column(String(128), default=None)
    body: Mapped[dict] = mapped_column(JSON, default=dict)


class ReadingSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chapter_id: Mapped[str] = mapped_column(String(32), ForeignKey("chapters.id"))
    learner_name: Mapped[str | None] = mapped_column(String(64), default=None)
    current_seg_id: Mapped[str | None] = mapped_column(String(64), default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)


class Event(Base):
    """行为流水，只增不改。"""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), index=True)
    seg_id: Mapped[str | None] = mapped_column(String(64), default=None)
    type: Mapped[str] = mapped_column(String(24))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LearnState(Base):
    __tablename__ = "learn_states"

    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), primary_key=True)
    goals: Mapped[dict] = mapped_column(JSON, default=dict)
    misconceptions: Mapped[dict] = mapped_column(JSON, default=dict)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class QuestionBook(Base):
    __tablename__ = "question_book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), index=True)
    question: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
