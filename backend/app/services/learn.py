"""学习状态：事件流水 → 目标 / 误区 / 画像。

写入策略：JSON 字段整体替换（不做原地修改），避免 SQLAlchemy 检测不到变更。
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Event, LearnState, ReadingSession

DEFAULT_GOAL = "untouched"  # untouched | in_progress | achieved


def _blank_goals(meta: dict) -> dict:
    return {gid: {"text": txt, "state": DEFAULT_GOAL} for gid, txt in meta.items()}


def _blank_misconceptions(meta: dict) -> dict:
    return {mid: {"text": txt, "state": "untouched"} for mid, txt in meta.items()}


def init_state(db: Session, session: ReadingSession, goals_meta: dict, misc_meta: dict) -> LearnState:
    st = LearnState(
        session_id=session.id,
        goals=_blank_goals(goals_meta),
        misconceptions=_blank_misconceptions(misc_meta),
        profile={
            "dwell_avg_ms": 0,
            "fast_skips": 0,
            "level_tries": 0,
            "questions": 0,
            "used_hooks": [],
            "last_dwell_ms": 0,
        },
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def get_state(db: Session, session_id: str) -> LearnState | None:
    return db.get(LearnState, session_id)


def recent_events(db: Session, session_id: str, limit: int = 40) -> list[Event]:
    rows = db.scalars(
        select(Event)
        .where(Event.session_id == session_id)
        .order_by(Event.id.desc())
        .limit(limit)
    )
    return list(rows)


def record_event(db: Session, session: ReadingSession, ev: Event) -> LearnState:
    """写事件，并增量维护画像。目标/误区的判定放在 agent 的 assess 节点里。"""
    db.add(ev)
    db.flush()

    st = get_state(db, session.id)
    if st is None:
        db.commit()
        return st  # 理论上不会发生

    profile = dict(st.profile or {})
    if ev.type == "dwell":
        ms = int((ev.payload or {}).get("ms", 0))
        profile["last_dwell_ms"] = ms
        avg = profile.get("dwell_avg_ms") or 0
        profile["dwell_avg_ms"] = int(avg * 0.7 + ms * 0.3) if avg else ms
        if ms < 2500:
            profile["fast_skips"] = int(profile.get("fast_skips", 0)) + 1
        else:
            profile["fast_skips"] = 0
    elif ev.type == "level_try":
        profile["level_tries"] = int(profile.get("level_tries", 0)) + 1
    elif ev.type == "ask":
        profile["questions"] = int(profile.get("questions", 0)) + 1

    st.profile = profile
    db.commit()
    db.refresh(st)
    return st


def set_goal(st: LearnState, goal_id: str, state: str) -> None:
    goals = dict(st.goals or {})
    if goal_id in goals:
        item = dict(goals[goal_id])
        item["state"] = state
        goals[goal_id] = item
        st.goals = goals


def set_misconception(st: LearnState, mis_id: str, state: str) -> None:
    misc = dict(st.misconceptions or {})
    if mis_id in misc:
        item = dict(misc[mis_id])
        item["state"] = state
        misc[mis_id] = item
        st.misconceptions = misc


def mark_hook_used(st: LearnState, hook_id: str) -> None:
    profile = dict(st.profile or {})
    used = list(profile.get("used_hooks", []))
    if hook_id not in used:
        used.append(hook_id)
    profile["used_hooks"] = used
    st.profile = profile
