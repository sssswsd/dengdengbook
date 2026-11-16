# 后端 · 等等，为什么？

FastAPI + SQLAlchemy + LangGraph。SQLite 起步，`DATABASE_URL` 可切 Postgres。

## 启动

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows
pip install -r requirements.txt

# 首次启动会自动建表并导入 seed/chapter_ch02.json
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

打开 http://127.0.0.1:8000/docs 看接口文档。

## 目录

```
backend/
├── app/
│   ├── main.py            FastAPI 入口、CORS、静态图片
│   ├── db.py              引擎与会话（SQLite ↔ Postgres 可切）
│   ├── models.py          7 张表
│   ├── schemas.py         出入参
│   ├── seed.py            seed/*.json → DB（幂等）
│   ├── api/
│   │   ├── chapters.py    章节
│   │   ├── sessions.py    会话 / 事件 / 状态
│   │   └── agent_api.py   ★ /next /ask /answer
│   ├── services/
│   │   ├── content.py     素材读取与主线推进
│   │   └── learn.py       事件 → 学习状态
│   └── agent/
│       ├── rules.py       ★ 决策规则（可单测）
│       ├── nodes.py       observe / assess / decide / select
│       └── graph.py       LangGraph 编排（缺失则顺序降级）
├── seed/
│   ├── chapter_ch02.json  第 2 章全部内容（主线 10 + 补充 3）
│   └── images/            插画
└── tests/test_rules.py
```

## 接口速查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查，返回当前 agent 引擎 |
| GET | `/api/chapters` | 章节列表 |
| POST | `/api/sessions` | 建会话 `{"chapter_id":"ch02"}` |
| POST | `/api/sessions/{id}/events` | 上报行为 `{"type":"dwell","seg_id":"seg_p08","payload":{"ms":1800}}` |
| **GET** | **`/api/sessions/{id}/next?current=seg_p08`** | **★ 后端决定下一个片段** |
| POST | `/api/sessions/{id}/ask` | 提问（SSE 流式） |
| POST | `/api/sessions/{id}/answer` | 关卡作答 `{"seg_id":"seg_p09","a":3,"b":5}` |
| GET | `/api/sessions/{id}/state` | 学习状态（面板用） |

## 三分钟验证"它是 agent"

```bash
# 1. 建会话
curl -s -X POST localhost:8000/api/sessions -H "Content-Type: application/json" \
     -d '{"chapter_id":"ch02"}' | tee /tmp/s.json

SID=$(python -c "import json;print(json.load(open('/tmp/s.json'))['id'])")

# 2. 快速翻过第 8 页（停 1.2 秒）
curl -s -X POST localhost:8000/api/sessions/$SID/events \
     -H "Content-Type: application/json" \
     -d '{"type":"dwell","seg_id":"seg_p08","payload":{"ms":1200}}'

curl -s "localhost:8000/api/sessions/$SID/next?current=seg_p08"
# → {"action":"insert","segment":{"id":"seg_x_example"...},"reason":"p08 只停了 1200ms..."}

# 3. 换一个会话，慢慢读（停 9 秒）
# → {"action":"continue","segment":{"id":"seg_p09"...}}
```

**同样的一页，两种读法，后端给出两种不同的答案。这就是系统要证明的东西。**

## 测试

```bash
.venv/Scripts/python -m pytest tests -q
```
