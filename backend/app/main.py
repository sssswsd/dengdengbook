"""FastAPI 入口。

启动：
    cd backend
    .venv/Scripts/uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .agent.graph import engine_name
from .api import agent_api, chapters, sessions
from .llm import client as llm_client
from .seed import SEED_DIR, seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    n = seed_if_empty()
    if n:
        print(f"[seed] imported {n} chapter(s)")
    print(f"[agent] engine = {engine_name()}")
    st = llm_client.status()
    print(f"[llm] enabled = {st['enabled']} model = {st['model']}")
    yield


app = FastAPI(
    title="等等，为什么？ · 后端",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chapters.router)
app.include_router(sessions.router)
app.include_router(agent_api.router)

app.mount("/images", StaticFiles(directory=str(SEED_DIR / "images")), name="images")


@app.get("/api/health")
def health():
    return {"ok": True, "agent_engine": engine_name(), "llm": llm_client.status()}
