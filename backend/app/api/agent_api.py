"""Agent 对外接口：下一个片段 / 提问 / 关卡作答。

这三个接口是"前端不算、后端算"的地方。
"""
import asyncio
import json
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import llm
from ..agent.graph import engine_name, run_agent
from ..db import get_db
from ..llm.prompts import build_messages
from ..models import Event, QuestionBook
from ..schemas import AnswerIn, AnswerOut, AskIn, LevelIn, LevelOut, NextOut
from ..services import content, learn, levels
from .sessions import _get_session, _state_out

router = APIRouter(prefix="/api/sessions", tags=["agent"])

# 本期没有接模型，先用人工写的答案。接口形状与接了模型完全一致。
# 注意：key 必须是"强特征词"。单个"为什么"不能算命中——孩子问恐龙为什么灭绝也会带上它。
CANNED: list[tuple[tuple[str, ...], str]] = [
    (
        ("3+5", "3 加 5", "算成 6", "算成6", "答成 6", "为什么错", "算错", "答错"),
        "它只见过 1+1、2+2 这样的题。它学到的办法是第一个数字加它自己，所以 3 加 5，它也算成 6。",
    ),
    (
        ("故意", "针对", "骗人", "它坏"),
        "故意得心里有想法。它没有。它只是照着见过的样子算。",
    ),
    (
        ("记住", "背下", "真的会", "学会了", "练习册"),
        "它把那一本练习册记住了。换一本没见过的，它就不一定了。",
    ),
]

OUT_OF_SCOPE = "这个我还答不上来。我先记在小本子上，下次我们一起看。"


@router.get("/{sid}/next", response_model=NextOut)
def next_segment(sid: str, current: str | None = None, db: Session = Depends(get_db)):
    """前端翻页时调这里。它不告诉前端"第几页"，只告诉它"接下来给他什么"。"""
    s = _get_session(db, sid)

    if current:
        seg = content.get_segment(db, current)
    else:
        seg = content.get_segment(db, s.current_seg_id) if s.current_seg_id else None

    out = run_agent(db, s, seg)

    st = learn.get_state(db, sid)
    if st is not None:
        st.goals = out.get("goals") or st.goals
        st.misconceptions = out.get("misconceptions") or st.misconceptions

        profile = dict(out.get("profile") or st.profile or {})
        if out.get("action") == "insert" and out.get("target"):
            used = list(profile.get("used_hooks", []))
            if out["target"] not in used:
                used.append(out["target"])
            profile["used_hooks"] = used
            if seg is not None and seg.seq is not None:
                profile["resume_after_seq"] = seg.seq
        st.profile = profile

        db.commit()
        db.refresh(st)
    else:
        st = learn.init_state(db, s, {}, {})

    target = content.get_segment(db, out["target"]) if out.get("target") else None

    return NextOut(
        action=out.get("action", "continue"),
        reason=out.get("reason", ""),
        segment=content.segment_out(target) if target else None,
        state=_state_out(st),
    )


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _save_question(sid: str, q: str) -> None:
    """流式生成器里不要复用请求级的 db，另开一个会话写。"""
    from ..db import SessionLocal

    d = SessionLocal()
    try:
        d.add(QuestionBook(session_id=sid, question=q))
        d.commit()
    finally:
        d.close()


def _sse_plain(text: str, in_scope: bool, via: str):
    def gen():
        for i in range(0, len(text), 2):
            yield _sse({"delta": text[i : i + 2]})
            time.sleep(0.016)
        yield _sse({"done": True, "in_scope": in_scope, "via": via, "engine": engine_name()})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _sse_llm(sid: str, q: str, messages: list[dict]):
    """大模型流式。首字超时 / 报错 / 跑题，一律回落到安全答案。"""
    collected: list[str] = []
    try:
        agen = llm.stream_answer(messages)
        first = await llm.first_token(agen)
        collected.append(first)
        yield _sse({"delta": first})

        async for delta in agen:
            collected.append(delta)
            yield _sse({"delta": delta})

        text = "".join(collected)
        refused = llm.is_refusal(text)
        if refused:
            _save_question(sid, q)
        yield _sse({"done": True, "in_scope": not refused, "via": "llm", "engine": engine_name()})

    except Exception as exc:  # 超时、网络、限流、模型抽风
        fallback = "……我先记在小本子上。" if collected else OUT_OF_SCOPE
        if not collected:
            _save_question(sid, q)
        for i in range(0, len(fallback), 2):
            yield _sse({"delta": fallback[i : i + 2]})
            await asyncio.sleep(0.015)
        yield _sse(
            {
                "done": True,
                "in_scope": False,
                "via": "fallback",
                "error": type(exc).__name__,
                "engine": engine_name(),
            }
        )


@router.post("/{sid}/ask")
async def ask(sid: str, payload: AskIn, db: Session = Depends(get_db)):
    """流式回答。

    三层：
      1. 规则快通道 —— 已知问题，零延迟零成本
      2. 大模型 —— 真正的自由对话，带本章上下文
      3. 降级 —— 没配 key / 超时 / 超次数，回落到安全答案
    """
    s = _get_session(db, sid)
    q = (payload.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="empty question")

    st = learn.get_state(db, sid)
    asked = int((st.profile or {}).get("questions", 0)) if st else 0
    goals = (st.goals if st else {}) or {}

    learn.record_event(
        db,
        s,
        Event(
            session_id=sid,
            seg_id=payload.seg_id,
            type="ask",
            payload={"question": q, "goal_tag": None},
        ),
    )

    # 1) 规则快通道
    for keys, text in CANNED:
        if any(k in q for k in keys):
            return _sse_plain(text, True, "rule")

    # 2) 大模型
    if llm.ENABLED and asked < llm.MAX_ASKS:
        seg = content.get_segment(db, payload.seg_id) if payload.seg_id else None
        chapter = content.get_chapter(db, s.chapter_id)
        messages = build_messages(
            q,
            chapter_title=chapter.title if chapter else "",
            summary=getattr(chapter, "summary", None),
            term=getattr(chapter, "term", None),
            seg_lines=(seg.body or {}).get("lines", []) if seg else [],
            goals=goals,
        )
        return StreamingResponse(
            _sse_llm(sid, q, messages),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # 3) 降级
    _save_question(sid, q)
    return _sse_plain(OUT_OF_SCOPE, False, "offline")


@router.post("/{sid}/level", response_model=LevelOut)
def level(sid: str, payload: LevelIn, db: Session = Depends(get_db)):
    """通用关卡。

    机器怎么反应由内容里的 `body.level.kind` 决定，这里只做分派。
    因此新增一种玩法不需要动这个接口，也不需要动 rules —— 这才是能加章的前提。
    """
    s = _get_session(db, sid)
    seg = content.get_segment(db, payload.seg_id)
    if seg is None:
        raise HTTPException(status_code=404, detail="segment not found")

    spec = (seg.body or {}).get("level") or {}
    kind = str(spec.get("kind") or "").strip()
    if not kind:
        raise HTTPException(status_code=400, detail="segment has no level spec")

    out = levels.run(kind, spec, payload.item_id, payload.action)

    learn.record_event(
        db,
        s,
        Event(
            session_id=sid,
            seg_id=payload.seg_id,
            type="level_try",
            payload={"kind": kind, "item": payload.item_id, "action": payload.action},
        ),
    )
    return LevelOut(**out)


@router.post("/{sid}/answer", response_model=AnswerOut)
def answer(sid: str, payload: AnswerIn, db: Session = Depends(get_db)):
    """旧接口，保留兼容。新代码走 /level。"""
    s = _get_session(db, sid)
    machine_answer = payload.a + payload.a  # ← 它的全部办法

    learn.record_event(
        db,
        s,
        Event(
            session_id=sid,
            seg_id=payload.seg_id,
            type="level_try",
            payload={"a": payload.a, "b": payload.b, "machine": machine_answer},
        ),
    )

    return AnswerOut(
        a=payload.a,
        b=payload.b,
        machine_answer=machine_answer,
        is_wrong=(payload.a + payload.b) != machine_answer,
        note="它把第一个数加了自己一次" if payload.a != payload.b else None,
    )
