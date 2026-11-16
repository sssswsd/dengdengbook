"""自由对话的健壮性测试。

不依赖真实网络：把 stream_answer 换成假的，验证三条兜底路径。
这才是演示时真正会出问题的三个地方。
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import llm  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def _session():
    r = client.post("/api/sessions", json={"chapter_id": "ch02"})
    return r.json()["id"]


def _ask(sid: str, q: str) -> str:
    r = client.post(
        f"/api/sessions/{sid}/ask",
        json={"question": q, "seg_id": "seg_p06"},
    )
    return r.text


def test_rule_path_hits_without_llm(monkeypatch):
    monkeypatch.setattr(llm, "ENABLED", False)
    body = _ask(_session(), "它为什么把 3+5 算成 6？")
    assert '"via": "rule"' in body
    assert '"in_scope": true' in body


def test_offline_when_llm_disabled(monkeypatch):
    monkeypatch.setattr(llm, "ENABLED", False)
    body = _ask(_session(), "这本书是谁画的？")
    assert '"via": "offline"' in body
    assert '"in_scope": false' in body


def test_fallback_when_model_errors(monkeypatch):
    monkeypatch.setattr(llm, "ENABLED", True)
    monkeypatch.setattr(llm, "MAX_ASKS", 30)

    async def boom(messages):
        raise RuntimeError("network down")
        yield ""  # pragma: no cover

    monkeypatch.setattr(llm, "stream_answer", boom)
    body = _ask(_session(), "这本书是谁画的？")
    assert '"via": "fallback"' in body
    assert "RuntimeError" in body


def test_fallback_when_first_token_times_out(monkeypatch):
    monkeypatch.setattr(llm, "ENABLED", True)

    async def slow(messages):
        import asyncio

        await asyncio.sleep(5)
        yield "太慢了"  # pragma: no cover

    async def immediate_timeout(agen, timeout=4):
        import asyncio

        raise asyncio.TimeoutError()

    monkeypatch.setattr(llm, "stream_answer", slow)
    monkeypatch.setattr(llm, "first_token", immediate_timeout)
    body = _ask(_session(), "这本书是谁画的？")
    assert '"via": "fallback"' in body


def test_refusal_detection():
    assert llm.is_refusal("这个我还答不上来，先记在小本子上。")
    assert not llm.is_refusal("它把第一个数加了自己一次。")
