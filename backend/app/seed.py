"""把 seed/*.json 灌进数据库。幂等：已存在则更新。"""
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine
from .models import Chapter, Segment

SEED_DIR = Path(__file__).resolve().parent.parent / "seed"


def upsert_chapter(db: Session, data: dict) -> None:
    meta = data["chapter"]
    ch = db.get(Chapter, meta["id"])
    if ch is None:
        ch = Chapter(id=meta["id"])
        db.add(ch)
    ch.title = meta["title"]
    ch.subtitle = meta.get("subtitle")
    ch.topic = meta.get("topic")
    ch.order_no = int(meta.get("order_no", 0))
    ch.goals_meta = data.get("goals", {})
    ch.misc_meta = data.get("misconceptions", {})
    ch.summary = data.get("summary")
    ch.term = data.get("term")

    for raw in data.get("segments", []):
        seg = db.get(Segment, raw["id"])
        if seg is None:
            seg = Segment(id=raw["id"])
            db.add(seg)
        seg.chapter_id = meta["id"]
        seg.seq = raw.get("seq")
        seg.kind = raw.get("kind", "story")
        seg.is_hook = int(raw.get("is_hook", 0))
        seg.is_checkpoint = int(raw.get("is_checkpoint", 0))
        seg.variant = raw.get("variant") or raw.get("body", {}).get("variant")
        seg.title = raw.get("title")
        seg.goal_tag = raw.get("goal_tag")
        seg.image = raw.get("image")
        seg.body = raw.get("body", {})

    # 内容里删掉的段落，库里也要删掉，否则改一版就留一堆孤儿页。
    keep = {raw["id"] for raw in data.get("segments", [])}
    if keep:
        db.query(Segment).filter(
            Segment.chapter_id == meta["id"], ~Segment.id.in_(keep)
        ).delete(synchronize_session=False)

    db.commit()


def _ensure_columns() -> None:
    """轻量 schema 迁移。SQLite 加列用 ALTER TABLE；换了 Postgres 再改这里。"""
    wanted = {
        "segments": [("is_checkpoint", "INTEGER DEFAULT 0")],
        "chapters": [("summary", "TEXT"), ("term", "TEXT")],
    }
    with engine.connect() as conn:
        for table, cols in wanted.items():
            rows = list(conn.exec_driver_sql(f"PRAGMA table_info({table})"))
            existing = {r[1] for r in rows}
            if not existing:
                continue
            for name, ddl in cols:
                if name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
                    conn.commit()


def seed_if_empty(force: bool = False) -> int:
    """返回导入的章节数。默认只在库为空时导入。"""
    Base.metadata.create_all(engine)
    _ensure_columns()
    db = SessionLocal()
    count = 0
    try:
        if not force and db.scalar(select(Chapter).limit(1)) is not None:
            return 0
        for path in sorted(SEED_DIR.glob("chapter_*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            upsert_chapter(db, data)
            count += 1
        return count
    finally:
        db.close()


if __name__ == "__main__":
    n = seed_if_empty(force=True)
    print(f"seeded {n} chapter(s)")
