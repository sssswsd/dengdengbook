"""会话、事件、状态接口。"""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Event, QuestionBook, ReadingSession
from ..schemas import EventIn, LearnStateOut, SessionCreate, SessionOut
from ..services import content, learn

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _state_out(st) -> LearnStateOut:
    return LearnStateOut(
        goals=st.goals or {}, misconceptions=st.misconceptions or {}, profile=st.profile or {}
    )


def _get_session(db: Session, sid: str) -> ReadingSession:
    s = db.get(ReadingSession, sid)
    if s is None:
        raise HTTPException(status_code=404, detail="session not found")
    return s


@router.post("", response_model=SessionOut)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    ch = content.get_chapter(db, payload.chapter_id)
    if ch is None:
        raise HTTPException(status_code=404, detail="chapter not found")

    first = content.first_segment(db, ch.id)
    if payload.start_seg:
        jump = content.get_segment(db, payload.start_seg)
        if jump is not None and jump.chapter_id == ch.id:
            first = jump
    s = ReadingSession(
        id=str(uuid4()),
        chapter_id=ch.id,
        learner_name=payload.learner_name,
        current_seg_id=first.id if first else None,
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    learn.init_state(db, s, ch.goals_meta or {}, ch.misc_meta or {})

    return SessionOut(
        id=s.id,
        chapter_id=s.chapter_id,
        learner_name=s.learner_name,
        current_seg_id=s.current_seg_id,
        first_segment=content.segment_out(first) if first else None,
    )


@router.get("/{sid}", response_model=SessionOut)
def get_session(sid: str, db: Session = Depends(get_db)):
    s = _get_session(db, sid)
    seg = content.get_segment(db, s.current_seg_id) if s.current_seg_id else None
    return SessionOut(
        id=s.id,
        chapter_id=s.chapter_id,
        learner_name=s.learner_name,
        current_seg_id=s.current_seg_id,
        first_segment=content.segment_out(seg) if seg else None,
    )


@router.post("/{sid}/events")
def post_event(sid: str, payload: EventIn, db: Session = Depends(get_db)):
    s = _get_session(db, sid)
    ev = Event(
        session_id=sid,
        seg_id=payload.seg_id,
        type=payload.type,
        payload=payload.payload or {},
    )
    st = learn.record_event(db, s, ev)

    if payload.type == "view" and payload.seg_id:
        s.current_seg_id = payload.seg_id
        db.commit()

    return {"ok": True, "state": _state_out(st) if st else None}


@router.get("/{sid}/state", response_model=LearnStateOut)
def get_state(sid: str, db: Session = Depends(get_db)):
    _get_session(db, sid)
    st = learn.get_state(db, sid)
    if st is None:
        raise HTTPException(status_code=404, detail="state not found")
    return _state_out(st)


@router.get("/{sid}/questions")
def list_questions(sid: str, db: Session = Depends(get_db)):
    """我的小本子：这个会话里它答不上来的问题。"""
    _get_session(db, sid)
    rows = db.scalars(
        select(QuestionBook).where(QuestionBook.session_id == sid).order_by(QuestionBook.id)
    ).all()
    return [
        {"id": r.id, "question": r.question, "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]
