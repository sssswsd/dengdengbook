"""把四个节点串成一条链路。

优先用 LangGraph 编译成状态图（可可视化、可回放、节点级可观测）；
如果环境里没装 LangGraph，退化成顺序调用，行为完全一致。
"""
from typing import Any

from .nodes import AgentState, assess, decide, observe, select

try:  # pragma: no cover
    from langgraph.graph import END, StateGraph

    HAS_LANGGRAPH = True
except Exception:  # pragma: no cover
    HAS_LANGGRAPH = False

_GRAPH = None


def _build():
    g = StateGraph(AgentState)
    g.add_node("observe", observe)
    g.add_node("assess", assess)
    g.add_node("decide", decide)
    g.add_node("select", select)
    g.set_entry_point("observe")
    g.add_edge("observe", "assess")
    g.add_edge("assess", "decide")
    g.add_edge("decide", "select")
    g.add_edge("select", END)
    return g.compile()


if HAS_LANGGRAPH:
    try:
        _GRAPH = _build()
    except Exception:  # pragma: no cover
        _GRAPH = None
        HAS_LANGGRAPH = False


def _sequential(state: AgentState) -> AgentState:
    for node in (observe, assess, decide, select):
        state.update(node(state))
    return state


def run_agent(db: Any, session: Any, seg: Any | None = None) -> AgentState:
    init: AgentState = {
        "db": db,
        "session": session,
        "seg_id": getattr(seg, "id", None),
        "seq": getattr(seg, "seq", None),
    }

    if _GRAPH is not None:
        try:
            return _GRAPH.invoke(init)
        except Exception:  # pragma: no cover
            pass

    return _sequential(init)


def engine_name() -> str:
    return "langgraph" if _GRAPH is not None else "sequential"
