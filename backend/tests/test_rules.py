"""决策规则单测。

这里的关键不是"某条规则对不对"，而是**规则不认识任何具体章节内容**。
所以测试里故意用虚构的片段 id——如果规则还能工作，说明它真的解耦了。
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.agent.rules import decide  # noqa: E402

HOOKS = [
    {"id": "x_plain", "goal": "G2", "title": "换个说法"},
    {"id": "x_probe", "goal": "G2", "title": "它是故意的吗"},
    {"id": "x_review", "goal": "G1", "title": "再看一眼"},
]


def base(**kw):
    ctx = {
        "seg_id": "any_page",
        "seq": 8,
        "is_checkpoint": True,
        "goal_tag": "G2",
        "title": "随便一页",
        "last_dwell_ms": 8000,
        "fast_skips": 0,
        "used_hooks": [],
        "misconceptions": {},
        "hooks": HOOKS,
    }
    ctx.update(kw)
    return ctx


def test_checkpoint_fast_skip_inserts_matching_hook():
    r = decide(base(last_dwell_ms=1200))
    assert r["action"] == "insert"
    assert r["target"] == "x_plain"
    assert "1200ms" in r["reason"]


def test_checkpoint_slow_read_continues():
    r = decide(base(last_dwell_ms=9000))
    assert r["action"] == "continue"


def test_non_checkpoint_never_interrupts():
    """普通页翻得再快也不打扰——只有关键页才需要盯。"""
    r = decide(base(is_checkpoint=False, last_dwell_ms=300))
    assert r["action"] == "continue"


def test_hook_not_repeated():
    r = decide(base(last_dwell_ms=1000, used_hooks=["x_plain"]))
    # 第一张用过了，按顺序拿下一张
    assert r["action"] == "insert"
    assert r["target"] != "x_plain"


def test_all_hooks_used_then_continue():
    r = decide(base(last_dwell_ms=1000, used_hooks=["x_plain", "x_probe", "x_review"]))
    assert r["action"] == "continue"


def test_goal_mismatch_does_not_insert():
    """目标对不上就不硬塞——这是换章能复用的关键。"""
    r = decide(base(last_dwell_ms=1000, goal_tag="G3"))
    assert r["action"] == "continue"


def test_misconception_m2_triggers_probe():
    r = decide(base(misconceptions={"M2": {"state": "triggered"}}))
    assert r["action"] == "insert"
    assert r["target"] == "x_probe"


def test_consecutive_fast_skips_pull_back():
    r = decide(base(fast_skips=3))
    assert r["action"] == "insert"
    assert r["target"] == "x_review"


def test_rules_do_not_hardcode_chapter_content():
    """换一个完全陌生的章节，规则照样工作。"""
    hooks = [{"id": "ch99_extra", "goal": "G1", "title": "另一个说法"}]
    r = decide(base(seg_id="seg99_p05", goal_tag="G1", hooks=hooks, last_dwell_ms=900))
    assert r["action"] == "insert"
    assert r["target"] == "ch99_extra"
