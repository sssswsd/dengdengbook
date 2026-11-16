"""Pydantic 出入参。"""
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChapterOut(BaseModel):
    id: str
    title: str
    subtitle: str | None = None
    topic: str | None = None
    order_no: int = 0
    segment_count: int = 0
    cover_url: str | None = None


class SegmentOut(BaseModel):
    id: str
    seq: int | None = None
    kind: str
    is_hook: int = 0
    variant: str | None = None
    title: str | None = None
    goal_tag: str | None = None
    image_url: str | None = None
    body: dict[str, Any] = Field(default_factory=dict)


class SessionCreate(BaseModel):
    chapter_id: str = "ch02"
    learner_name: str | None = None
    # 直接落到某一段，用于演示和调试（?ch=ch05&seg=seg5_p07）。
    start_seg: str | None = None


class SessionOut(BaseModel):
    id: str
    chapter_id: str
    learner_name: str | None = None
    current_seg_id: str | None = None
    first_segment: SegmentOut | None = None


EventType = Literal[
    "view", "dwell", "bubble_click", "ask", "answer", "level_try", "finish"
]


class EventIn(BaseModel):
    type: EventType
    seg_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class LearnStateOut(BaseModel):
    goals: dict[str, Any]
    misconceptions: dict[str, Any]
    profile: dict[str, Any]


class NextOut(BaseModel):
    action: str
    reason: str
    segment: SegmentOut | None = None
    state: LearnStateOut


class AskIn(BaseModel):
    question: str
    seg_id: str | None = None


class AnswerIn(BaseModel):
    seg_id: str
    a: int
    b: int


class AnswerOut(BaseModel):
    a: int
    b: int
    machine_answer: int
    is_wrong: bool
    note: str | None = None


class LevelIn(BaseModel):
    """通用关卡请求。kind 之后的行为由内容里的 level.kind 决定。"""

    seg_id: str
    item_id: str = ""
    action: dict = Field(default_factory=dict)


class LevelOut(BaseModel):
    machine: dict
    error: str | None = None
