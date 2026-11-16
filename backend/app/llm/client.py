"""大模型接入。

设计原则：**没有 key 也能跑。**
- 未配置 LLM_API_KEY 时自动关闭，`/ask` 回落到人工答案库
- 配了 key 就自动启用，接口形状完全不变
- 首字超时 / 报错 / 跑题，一律回落，绝不让演示卡住
"""
import asyncio
import os

BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
API_KEY = (os.getenv("LLM_API_KEY") or "").strip()
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

ENABLED = os.getenv("LLM_ENABLED", "1") == "1" and bool(API_KEY)
FIRST_TOKEN_TIMEOUT = float(os.getenv("LLM_FIRST_TOKEN_TIMEOUT", "4"))
TOTAL_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "20"))
MAX_ASKS = int(os.getenv("LLM_MAX_ASKS", "30"))

REFUSAL_MARK = "答不上来"

_client = None
if ENABLED:
    try:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TOTAL_TIMEOUT)
    except Exception:  # pragma: no cover
        ENABLED = False
        _client = None


def status() -> dict:
    return {
        "enabled": bool(ENABLED),
        "model": MODEL if ENABLED else None,
        "first_token_timeout": FIRST_TOKEN_TIMEOUT,
        "max_asks_per_session": MAX_ASKS,
    }


async def stream_answer(messages: list[dict]):
    """逐 token 产出。调用方负责首字超时与异常回落。"""
    if _client is None:
        raise RuntimeError("llm disabled")

    stream = await _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        stream=True,
        temperature=0.6,
        max_tokens=220,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def first_token(agen, timeout: float = FIRST_TOKEN_TIMEOUT):
    """等第一个 token，超时就认为这次不靠谱。"""
    return await asyncio.wait_for(agen.__anext__(), timeout)


def is_refusal(text: str) -> bool:
    """模型自己承认答不上来 —— 这句话同时是"超纲"的信号。"""
    return REFUSAL_MARK in text
