"""关卡引擎测试。

这些测试故意用虚构的章节数据，确认引擎不认识任何具体章节。
"""
from app.services import levels


def test_kinds_registered():
    assert {"arithmetic", "confidence", "label", "sort"} <= set(levels.kinds())


def test_unknown_kind_does_not_crash():
    out = levels.run("nope", {}, "x", {})
    assert out["machine"]["text"] == "—"
    assert "unknown" in out["error"]


def test_arithmetic_always_adds_to_itself():
    spec = {"items": [{"id": "q1", "a": 3, "b": 5}, {"id": "q2", "a": 9, "b": 9}]}
    r1 = levels.run("arithmetic", spec, "q1", {})
    assert r1["machine"]["text"] == "3 + 5 = 6"
    assert r1["machine"]["wrong"] is True

    r2 = levels.run("arithmetic", spec, "q2", {})
    assert r2["machine"]["text"] == "9 + 9 = 18"
    assert r2["machine"]["wrong"] is False


def test_confidence_is_always_full():
    spec = {"items": [{"id": "a", "q": "天为什么蓝", "answer": "因为画上去的", "ok": False}]}
    r = levels.run("confidence", spec, "a", {})
    assert r["machine"]["confidence"] == 100
    assert r["machine"]["correct"] is False


def _label_spec():
    return {
        "unknown_words": ["不知道"],
        "targets": [
            {"id": "t1", "name": "穿山甲", "from": "ph1", "fallback": "刺猬"},
            {"id": "t2", "name": "貘", "from": "ph2", "fallback": "猪"},
        ],
    }


def test_label_uses_childs_tag():
    """孩子标了「刺猬」，它就真的答刺猬 —— 它认的是标签，不是照片。"""
    r = levels.run("label", _label_spec(), "t1", {"labels": {"ph1": "刺猬"}})
    assert r["machine"]["text"] == "刺猬"
    assert r["machine"]["right"] is False
    assert r["machine"]["because"] == "你标过"


def test_label_invents_when_unlabeled():
    """孩子没标，它也不说不知道，而是硬挑一个最像的。"""
    r = levels.run("label", _label_spec(), "t1", {"labels": {"ph1": "不知道"}})
    assert r["machine"]["text"] == "刺猬"
    assert r["machine"]["because"] == "它没见过，就挑了个最像的"


def test_label_is_right_if_child_taught_it():
    r = levels.run("label", _label_spec(), "t1", {"labels": {"ph1": "穿山甲"}})
    assert r["machine"]["right"] is True


def test_label_commit_counts_only_known():
    spec = _label_spec()
    r = levels.run(
        "label",
        spec,
        "",
        {"step": "commit", "labels": {"ph1": "刺猬", "ph2": "不知道", "ph3": ""}},
    )
    assert r["machine"]["known"] == ["ph1"]
    assert "1" in r["machine"]["text"]


def test_sort_never_judges():
    spec = {"bins": [{"id": "its"}, {"id": "mine"}]}
    r = levels.run("sort", spec, "", {"placed": {"a": "its", "b": "its", "c": "mine"}})
    assert r["machine"]["counts"] == {"its": 2, "mine": 1}
    assert r["machine"]["no_answer"] is True


def test_missing_item_is_safe():
    for kind, spec in [("arithmetic", {"items": []}), ("confidence", {"items": []}),
                       ("label", {"targets": []})]:
        r = levels.run(kind, spec, "ghost", {})
        assert r["machine"]["text"] == "—"


def test_stripes_flips_at_threshold_and_stays_certain():
    spec = {"base": "猫", "other": "斑马", "flip_at": 3}
    for n in range(4):
        r = levels.run("stripes", spec, "", {"stripes": n})
        assert r["machine"]["label"] == ("斑马" if n >= 3 else "猫")
    lo = levels.run("stripes", spec, "", {"stripes": 2})["machine"]
    hi = levels.run("stripes", spec, "", {"stripes": 3})["machine"]
    assert lo["confidence"] >= 96 and hi["confidence"] >= 96
    assert hi["flipped"] is True


def test_prompt_returns_what_content_wrote():
    spec = {"items": [{"id": "q1", "ask": "盒子里有几颗？", "say": "三颗。", "follows": "数量"}]}
    r = levels.run("prompt", spec, "q1", {})["machine"]
    assert r["text"] == "三颗。"
    assert r["follows"] == "数量"


def test_chain_marks_false_statement():
    spec = {"items": [{"id": "c1", "seed": "鱼在天上游泳", "out": "云是它的河。", "true": False}]}
    r = levels.run("chain", spec, "c1", {})["machine"]
    assert r["true_statement"] is False
    assert r["text"] == "云是它的河。"


def test_feed_picks_most_clicked():
    r = levels.run("feed", {}, "", {"seen": ["恐龙", "恐龙", "星星", "恐龙", "恐龙"]})
    m = r["machine"]
    assert m["top"] == "恐龙"
    assert m["share"] == 80


def test_feed_empty_is_safe():
    assert levels.run("feed", {}, "", {})["machine"]["top"] is None


def test_memory_drops_oldest_beyond_slots():
    r = levels.run("memory", {"slots": 3}, "", {"remember": ["a", "b", "c", "d", "e"]})
    m = r["machine"]
    assert m["kept"] == ["c", "d", "e"]
    assert m["dropped"] == ["a", "b"]
    assert m["full"] is True


def _knn_spec():
    return {
        "points": [
            {"id": "a", "x": 10, "y": 10, "label": "苹果"},
            {"id": "b", "x": 20, "y": 50, "label": "苹果"},
            {"id": "c", "x": 30, "y": 20, "label": "梨"},
            {"id": "d", "x": 90, "y": 90, "label": "梨"},
        ],
        "queries": [{"id": "q1", "x": 12, "y": 12}],
    }


def test_knn_k1_listens_to_nearest_only():
    m = levels.run("knn", _knn_spec(), "", {"q": "q1", "k": 1})["machine"]
    assert m["neighbors"][0]["label"] == "苹果"
    assert m["label"] == "苹果"
    assert m["share"] == 100


def test_knn_k3_votes_by_majority():
    m = levels.run("knn", _knn_spec(), "", {"q": "q1", "k": 3})["machine"]
    assert m["label"] == "苹果"
    assert m["votes"] == {"苹果": 2, "梨": 1}
    assert m["share"] == 67


def test_knn_k_larger_than_points_is_clamped():
    m = levels.run("knn", _knn_spec(), "", {"q": "q1", "k": 99})["machine"]
    assert m["k"] == 4


def test_knn_tie_goes_to_closest():
    spec = {
        "points": [
            {"id": "a", "x": 0, "y": 10, "label": "苹果"},
            {"id": "b", "x": 0, "y": 20, "label": "梨"},
        ],
        "queries": [{"id": "q", "x": 0, "y": 0}],
    }
    m = levels.run("knn", spec, "", {"q": "q", "k": 2})["machine"]
    assert m["votes"] == {"苹果": 1, "梨": 1}
    assert m["label"] == "苹果"


def test_knn_missing_query_is_safe():
    assert levels.run("knn", _knn_spec(), "", {"q": "nope", "k": 3})["machine"]["text"] == "—"


# ---------- cnn（第 7 章：切格子看画） ----------

def _cnn_spec():
    return {
        "answer": "猫",
        "options": ["斑马", "猫"],
        "tiles": [
            {"id": "t1", "x": 0, "y": 0, "see": "竖条纹", "vote": "斑马"},
            {"id": "t2", "x": 1, "y": 0, "see": "耳朵", "vote": "猫"},
            {"id": "t3", "x": 2, "y": 0, "see": "胡须", "vote": "猫"},
        ],
    }


def test_cnn_few_tiles_guesses_wrong():
    m = levels.run("cnn", _cnn_spec(), "", {"revealed": ["t1"]})["machine"]
    assert m["label"] == "斑马"
    assert m["share"] == 100


def test_cnn_all_tiles_guesses_right():
    m = levels.run("cnn", _cnn_spec(), "", {"revealed": ["t1", "t2", "t3"]})["machine"]
    assert m["label"] == "猫"
    assert m["votes"] == {"斑马": 1, "猫": 2}


def test_cnn_tie_keeps_first_seen():
    m = levels.run("cnn", _cnn_spec(), "", {"revealed": ["t1", "t2"]})["machine"]
    assert m["votes"] == {"斑马": 1, "猫": 1}
    assert m["label"] == "斑马"


def test_cnn_no_tiles_is_safe():
    assert levels.run("cnn", _cnn_spec(), "", {"revealed": []})["machine"]["text"] == "—"


# ---------- rnn（第 8 章：说到后面忘了前面） ----------

def _rnn_spec():
    return {
        "rounds": [
            {"id": "r1", "text": "小猫追蝴蝶"},
            {"id": "r2", "text": "小猫追蝴蝶穿过了花园跳过了篱笆"},
        ],
    }


def test_rnn_short_sentence_remembered_all():
    m = levels.run("rnn", _rnn_spec(), "", {"round": "r1"})["machine"]
    assert m["forgot"] == 0
    assert m["remembered"] == "小猫追蝴蝶"


def test_rnn_long_sentence_drops_head():
    m = levels.run("rnn", _rnn_spec(), "", {"round": "r2"})["machine"]
    assert m["forgot"] > 0
    assert m["remembered"].endswith("跳过了篱笆")
    assert m["dropped"].startswith("小猫")


def test_rnn_missing_round_is_safe():
    assert levels.run("rnn", _rnn_spec(), "", {"round": "nope"})["machine"]["text"] == "—"


def test_new_kinds_are_registered():
    ks = levels.kinds()
    assert "cnn" in ks
    assert "rnn" in ks
