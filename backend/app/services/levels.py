"""关卡引擎：机器行为模型。

每一种 kind 描述的是「这台机器会怎么反应」，不是某一章的具体玩法。
内容文件只选 kind 并填数据，因此加新章节不需要改这里的代码。

新增一种玩法 = 在这里加一个 handler + 前端加一个组件，两者靠 kind 对齐。
"""
from __future__ import annotations

from typing import Any

Handler = Any


def _index(items: list[dict]) -> dict[str, dict]:
    return {str(it["id"]): it for it in items}


def _arithmetic(spec: dict, item_id: str, action: dict) -> dict:
    """它以为所有题都是「一个数加它自己」。

    这是第 2 章的机器：见过的一百道全是 a+a，于是它学到的办法就是 a+a。
    """
    it = _index(spec.get("items", [])).get(item_id)
    if not it:
        return {"machine": {"kind": "arithmetic", "text": "—"}}
    a, b = int(it["a"]), int(it["b"])
    ans = a + a
    return {
        "machine": {
            "kind": "arithmetic",
            "text": f"{a} + {b} = {ans}",
            "wrong": ans != a + b,
        }
    }


def _confidence(spec: dict, item_id: str, action: dict) -> dict:
    """它答什么都一样有把握。

    第 3 章的机器：confidence 恒为 100，答对答错都如此。
    """
    it = _index(spec.get("items", [])).get(item_id)
    if not it:
        return {"machine": {"kind": "confidence", "text": "—"}}
    return {
        "machine": {
            "kind": "confidence",
            "question": it.get("q"),
            "text": it.get("answer", ""),
            "confidence": 100,
            "correct": bool(it.get("ok", False)),
        }
    }


def _label(spec: dict, item_id: str, action: dict) -> dict:
    """它的认识清单，就是别人贴给它的标签。

    第 4 章的机器：孩子给照片贴了什么标签，它就认识什么。
    孩子没标的（或标了「不知道」的），它不会承认不知道，
    而是拿清单里最像的一个硬套上去 —— 这才是这一章真正要讲的事。
    """
    labels: dict[str, str] = action.get("labels") or {}
    unknown_words = set(spec.get("unknown_words") or ["不知道"])

    def _known(photo_id: str) -> str | None:
        v = labels.get(photo_id)
        if not v or v in unknown_words:
            return None
        return v

    if action.get("step") == "commit":
        known = [pid for pid in labels if _known(pid)]
        return {
            "machine": {
                "kind": "commit",
                "known": known,
                "text": f"记住了 {len(known)} 个。",
            }
        }

    t = _index(spec.get("targets", [])).get(item_id)
    if not t:
        return {"machine": {"kind": "label", "text": "—"}}

    got = _known(str(t.get("from", "")))
    said = got or t.get("fallback") or "不知道"
    return {
        "machine": {
            "kind": "label",
            "target": t.get("name"),
            "text": said,
            "right": said == t.get("name"),
            "because": "你标过" if got else "它没见过，就挑了个最像的",
        }
    }


def _sort(spec: dict, item_id: str, action: dict) -> dict:
    """没有标准答案的分类关卡（第 10 章用）。

    引擎只记录孩子怎么分的，不做判定 —— 判定本身就是这一章要反对的事。
    """
    placed: dict[str, str] = action.get("placed") or {}
    bins = spec.get("bins") or []
    counts = {b["id"]: 0 for b in bins}
    for _, bid in placed.items():
        if bid in counts:
            counts[bid] += 1
    return {"machine": {"kind": "sort", "counts": counts, "no_answer": True}}


def _stripes(spec: dict, item_id: str, action: dict) -> dict:
    """几条线就能把它带偏，而且改口的时候一样确定。第 5 章的机器。

    它分不清「条纹长在动物身上」和「线条画在照片上」——
    对它来说，进来的一样都是深浅不一的像素。
    """
    n = int(action.get("stripes") or 0)
    flip_at = int(spec.get("flip_at") or 3)
    base = spec.get("base") or "猫"
    other = spec.get("other") or "斑马"

    flipped = n >= flip_at
    return {
        "machine": {
            "kind": "stripes",
            "stripes": n,
            "label": other if flipped else base,
            "confidence": 96 + min(n, 3),
            "flipped": flipped,
        }
    }


def _prompt(spec: dict, item_id: str, action: dict) -> dict:
    """它答的是你问的那句话，不是那个东西。第 6 章的机器。

    内容里每条都写清了它怎么顺着问法走，引擎只负责取出来 ——
    因为「它跟着哪个词走」是要给答辩看的，不能藏在代码里。
    """
    it = _index(spec.get("items", [])).get(item_id)
    if not it:
        return {"machine": {"kind": "prompt", "text": "—"}}
    return {
        "machine": {
            "kind": "prompt",
            "ask": it.get("ask"),
            "text": it.get("say", ""),
            "follows": it.get("follows"),
            "note": it.get("note"),
        }
    }


def _chain(spec: dict, item_id: str, action: dict) -> dict:
    """它不是在想下一句，是在接下一句。第 7 章的机器。

    所以内容里可以写：给它一句假的，它照样接得很美。
    """
    it = _index(spec.get("items", [])).get(item_id)
    if not it:
        return {"machine": {"kind": "chain", "text": "—"}}
    return {
        "machine": {
            "kind": "chain",
            "seed": it.get("seed"),
            "text": it.get("out", ""),
            "note": it.get("note"),
            "true_statement": bool(it.get("true", True)),
        }
    }


def _feed(spec: dict, item_id: str, action: dict) -> dict:
    """它推的是你点过的，不是你想看的。第 8 章的机器。"""
    seen: list[str] = list(action.get("seen") or [])
    counts: dict[str, int] = {}
    for t in seen:
        counts[t] = counts.get(t, 0) + 1

    if not counts:
        return {"machine": {"kind": "feed", "counts": {}, "top": None, "total": 0}}

    top = max(counts, key=lambda k: (counts[k], -seen.index(k)))
    total = len(seen)
    return {
        "machine": {
            "kind": "feed",
            "counts": counts,
            "top": top,
            "total": total,
            "share": round(counts[top] / total * 100),
        }
    }


def _memory(spec: dict, item_id: str, action: dict) -> dict:
    """它只留得住最近的几条，再往前就掉出去了。第 9 章的机器。

    注意这不是「记得不牢」，是「根本没有存」——
    所以它会很礼貌地再问一次「你是谁」，而不是答得含糊。
    """
    slots = int(spec.get("slots") or 6)
    remember: list[str] = list(action.get("remember") or [])
    return {
        "machine": {
            "kind": "memory",
            "slots": slots,
            "kept": remember[-slots:] if slots > 0 else [],
            "dropped": remember[:-slots] if len(remember) > slots else [],
            "full": len(remember) >= slots,
        }
    }


def _knn(spec: dict, item_id: str, action: dict) -> dict:
    """它不认识这个东西，它只找最近的几个邻居投票。第 9 章的机器。

    k 就是「看几个邻居」。k=1 时最近那个说了算，容易被一个怪东西带偏；
    k 大一点更稳，但边界会糊。这一关值钱的地方就在这里 ——
    孩子能亲手看见「看几个」会改变答案。
    """
    points = spec.get("points") or []
    k = int(action.get("k") or 3)
    qid = action.get("q") or item_id
    q = _index(spec.get("queries") or []).get(str(qid))
    if not q or not points:
        return {"machine": {"kind": "knn", "text": "—"}}

    qx, qy = float(q["x"]), float(q["y"])
    ranked = sorted(
        (
            {
                "id": p.get("id"),
                "label": p.get("label", "?"),
                "d": int(round(((p["x"] - qx) ** 2 + (p["y"] - qy) ** 2) ** 0.5)),
            }
            for p in points
        ),
        key=lambda r: r["d"],
    )
    k = max(1, min(k, len(ranked)))
    near = ranked[:k]

    votes: dict[str, int] = {}
    for n in near:
        votes[n["label"]] = votes.get(n["label"], 0) + 1
    # 票数一样时，听最近那个的
    order = [n["label"] for n in near]
    top = max(votes, key=lambda lb: (votes[lb], -order.index(lb)))

    return {
        "machine": {
            "kind": "knn",
            "k": k,
            "neighbors": near,
            "votes": votes,
            "label": top,
            "share": round(votes[top] / k * 100),
        }
    }


def _cnn(spec: dict, item_id: str, action: dict) -> dict:
    """它不看整幅画，它一格一格看，最后拼起来投票。第 7 章的机器。

    孩子翻开几个格子，它就只看几个格子。翻得少时票数被个别格子带偏
    （比如两个条纹格 → 猜斑马），全翻开才拼出正确答案。
    这一关的机器行为：已翻开格子的 vote 计多数票，平票时听先翻开的那格。
    """
    tiles = spec.get("tiles") or []
    revealed = [str(r) for r in (action.get("revealed") or [])]
    if not tiles or not revealed:
        return {"machine": {"kind": "cnn", "text": "—"}}

    by_id = _index(tiles)
    seen: list[dict] = []
    for rid in revealed:
        t = by_id.get(rid)
        if t:
            seen.append({"id": rid, "see": t.get("see", ""), "vote": t.get("vote", "?")})
    if not seen:
        return {"machine": {"kind": "cnn", "text": "—"}}

    votes: dict[str, int] = {}
    for s in seen:
        votes[s["vote"]] = votes.get(s["vote"], 0) + 1
    order = [s["vote"] for s in seen]
    top = max(votes, key=lambda lb: (votes[lb], -order.index(lb)))
    total = len(seen)

    return {
        "machine": {
            "kind": "cnn",
            "seen": seen,
            "votes": votes,
            "label": top,
            "share": round(votes[top] / total * 100),
            "opened": f"{total}/{len(tiles)}",
        }
    }


def _rnn(spec: dict, item_id: str, action: dict) -> dict:
    """它一句一句往后传，手里只留一点点地方：新的进来，旧的滑走。第 8 章的机器。

    句子越长，它记得的越少——记住的永远是「最后几个字」。
    这一关的机器行为：记的是末尾一段，长度随句子变长而缩短。
    """
    rounds = spec.get("rounds") or []
    rid = str(action.get("round") or item_id)
    r = _index(rounds).get(rid)
    if not r:
        return {"machine": {"kind": "rnn", "text": "—"}}

    text = str(r.get("text", ""))
    n = len(text)
    # 记忆容量：短句全记得，长句只剩末尾几个字
    keep = max(3, 11 - n // 3)
    remembered = text[-keep:] if n > keep else text
    forgot = n - len(remembered)

    return {
        "machine": {
            "kind": "rnn",
            "length": n,
            "remembered": remembered,
            "forgot": forgot,
            "text": (f"它只记得：「{remembered}」" if forgot else f"它全记得：「{text}」"),
            "dropped": text[:forgot] if forgot else "",
        }
    }


_HANDLERS: dict[str, Handler] = {
    "arithmetic": _arithmetic,
    "confidence": _confidence,
    "label": _label,
    "sort": _sort,
    "stripes": _stripes,
    "prompt": _prompt,
    "chain": _chain,
    "feed": _feed,
    "memory": _memory,
    "knn": _knn,
    "cnn": _cnn,
    "rnn": _rnn,
}


def kinds() -> list[str]:
    return sorted(_HANDLERS)


def run(kind: str, spec: dict, item_id: str, action: dict | None = None) -> dict:
    fn = _HANDLERS.get(kind)
    if fn is None:
        return {"machine": {"kind": "unknown", "text": "—"}, "error": f"unknown level kind: {kind}"}
    return fn(spec or {}, item_id, action or {})
