"""Agent 的四个节点：观察 → 评估 → 决策 → 选取。"""
from typing import Any, TypedDict

from ..services import content, learn
from . import rules


class AgentState(TypedDict, total=False):
    db: Any                 # Session（不参与序列化，仅用于读库）
    session: Any            # ReadingSession
    seg_id: str | None      # 当前所在片段
    seq: int | None
    recent: list            # 最近的原始事件
    goals: dict
    misconceptions: dict
    profile: dict
    action: str
    target: str | None
    reason: str


def observe(state: AgentState) -> dict:
    """拉最近的流水，和当前学习状态。"""
    db = state["db"]
    session = state["session"]
    st = learn.get_state(db, session.id)
    evs = learn.recent_events(db, session.id)
    return {
        "recent": [
            {"type": e.type, "seg_id": e.seg_id, "payload": e.payload or {}} for e in evs
        ],
        "goals": dict(st.goals or {}) if st else {},
        "misconceptions": dict(st.misconceptions or {}) if st else {},
        "profile": dict(st.profile or {}) if st else {},
    }


def assess(state: AgentState) -> dict:
    """把行为翻译成"目标达成情况"和"误区是否触发"。纯内存计算，由调用方落库。"""
    goals = dict(state.get("goals") or {})
    misc = dict(state.get("misconceptions") or {})
    recent = state.get("recent") or []
    profile = state.get("profile") or {}

    def touch(box: dict, key: str, value: str) -> None:
        if key in box:
            item = dict(box[key])
            item["state"] = value
            box[key] = item

    for e in recent:
        if e["type"] == "bubble_click":
            tag = e["payload"].get("goal_tag")
            if tag:
                touch(goals, tag, "achieved")
        elif e["type"] == "answer" and e["payload"].get("correct"):
            touch(goals, "G3", "achieved")
        elif e["type"] == "ask":
            q = str(e["payload"].get("question", ""))
            if any(k in q for k in ("故意", "针对", "坏")):
                touch(misc, "M2", "triggered")

    # 关卡试过就说明在探索；试够 3 道认为 G3 达成
    tries = int(profile.get("level_tries") or 0)
    if tries >= 1:
        touch(goals, "G3", "achieved" if tries >= 3 else "in_progress")

    # 在任何一页"关键页"上停够了，就认为它对应的目标达成。
    # 注意：这里按 goal_tag 认，不按具体片段 id —— 换章不用改。
    seg = content.get_segment(state["db"], state["seg_id"]) if state.get("seg_id") else None
    if seg is not None and seg.is_checkpoint and seg.goal_tag:
        if int(profile.get("last_dwell_ms") or 0) >= rules.SKIP_THRESHOLD_MS:
            touch(goals, seg.goal_tag, "achieved")

    return {"goals": goals, "misconceptions": misc}


def decide(state: AgentState) -> dict:
    """组装决策上下文。规则本身不认识具体片段，只认识"这一页是什么性质"。"""
    db = state["db"]
    session = state["session"]
    profile = state.get("profile") or {}
    seg = content.get_segment(db, state["seg_id"]) if state.get("seg_id") else None

    ctx = {
        "seg_id": state.get("seg_id"),
        "seq": state.get("seq"),
        "is_checkpoint": bool(getattr(seg, "is_checkpoint", 0)),
        "goal_tag": getattr(seg, "goal_tag", None),
        "title": getattr(seg, "title", None),
        "last_dwell_ms": profile.get("last_dwell_ms"),
        "fast_skips": profile.get("fast_skips"),
        "used_hooks": profile.get("used_hooks"),
        "misconceptions": state.get("misconceptions"),
        "hooks": content.hook_index(db, session.chapter_id),
    }
    res = rules.decide(ctx)
    return {"action": res["action"], "target": res["target"], "reason": res["reason"]}


def select(state: AgentState) -> dict:
    """校验要给的片段确实存在；不存在就老实退回主线。"""
    db = state["db"]
    session = state["session"]
    action = state.get("action")
    target = state.get("target")

    if action == "insert" and target:
        seg = content.get_segment(db, target)
        if seg is not None and seg.chapter_id == session.chapter_id:
            return {}

    if action in ("continue", "insert"):
        cur = content.get_segment(db, state["seg_id"]) if state.get("seg_id") else None
        profile = state.get("profile") or {}
        # 如果当前停在"补充牌"上（seq 为空），从上次插入时的主线位置继续
        anchor = cur.seq if cur is not None and cur.seq is not None else profile.get("resume_after_seq")
        nxt = content.next_main(db, session.chapter_id, anchor)
        if nxt is None:
            return {
                "action": "finish",
                "target": None,
                "reason": "这一本已经读到最后一页了",
            }
        return {"action": "continue", "target": nxt.id}

    return {}
