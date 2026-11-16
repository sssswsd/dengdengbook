# 等等，为什么？

一个面向 7–9 岁儿童的 AI 科普阅读系统。**内容（绘本、插画、故事）是数据，产品是「观察 → 判断 → 决定给他什么」的闭环。**

## 这个系统在做什么

普通电子绘本，翻到第 8 页就是第 8 页，每个孩子看到的都一样。

这个系统里，**前端不知道下一页是什么，它问后端**：

```
前端翻页 → GET /api/sessions/{id}/next?current=seg_p08
                ↓
        后端跑 Agent 图
        observe → assess → decide → select
                ↓
     { action: "insert", segment: {...}, reason: "只停了 1.2s，太快" }
```

同一个孩子快读和慢读，会读到不同的页。这是系统要证明的唯一一件事。

## 目录

```
├── backend/            FastAPI + SQLAlchemy + LangGraph
│   ├── app/
│   │   ├── api/        章节 / 会话 / agent 接口
│   │   ├── services/   内容读取、学习状态
│   │   └── agent/      决策规则 + 状态图
│   ├── seed/           第 2 章全部内容（主线 10 段 + 补充 3 段）
│   └── tests/          决策规则单测
├── frontend/           React + Vite + TS
│   └── src/            阅读器、对话、agent 面板
├── docs/               需求、PRD、系统设计、内容稿
├── art/                插画源文件
└── docker-compose.yml
```

## 跑起来

**后端**

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

首次启动会自动建表并导入 `seed/chapter_ch02.json`。接口文档：http://127.0.0.1:8000/docs

**前端**

```bash
cd frontend
npm install
npm run dev
```

打开 http://127.0.0.1:5173

**一键（Docker）**

```bash
docker compose up
```

## 三分钟看它是 agent

1. 打开前端，一路**快点**翻过第 8 页（"它学的不是加法"）
2. 右上角提示「后端决定插入一段」，中间多出一页**红苹果 / 青苹果**
3. 刷新重来，在第 8 页**停 8 秒**再翻
4. 这次没有插入，直接进关卡

右侧面板会实时显示后端的判断：`本次动作 / 理由 / 教学目标 / 误区 / 画像`。

## 文档

| 文件 | 内容 |
|---|---|
| `docs/07-系统设计.md` | 架构、数据库、接口、Agent 图、里程碑 |
| `docs/02-PRD.md` | 产品需求 |
| `docs/01-需求分析.md` | 需求分析 |
| `docs/04-第2章内容稿-它背下了整本练习册.md` | 章节内容（系统种子数据的来源） |
| `docs/06-插画出图手册.md` | 补内容时的出图规范 |
| `docs/08-系统演进建议.md` | 下一步该加什么，以及为什么 |

> `index.html` 是早期的单文件视觉原型，**不是交付物**，仅作参考。

## 大模型自由对话（可选）

不配 key 也能跑：`/ask` 会回落到人工答案库，整章功能不受影响。

要开自由对话：

```bash
cd backend
cp .env.example .env
# 填 LLM_API_KEY（DeepSeek 或智谱），然后重启后端
```

护栏：首字 4 秒超时、异常自动回落、单会话限 30 次、无关问题直接记本子。
`/api/health` 里能看 `llm.enabled`；`/ask` 返回的 `via` 字段会告诉你走的是 `rule` / `llm` / `offline` / `fallback`。

**答辩想稳**：临时设 `LLM_ENABLED=0`，全部走预置答案。
