"""内容读取与推进。所有"下一段是什么"的判断都不在这里——这里只提供素材。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Chapter, Segment
from ..schemas import SegmentOut


def segment_out(seg: Segment) -> SegmentOut:
    return SegmentOut(
        id=seg.id,
        seq=seg.seq,
        kind=seg.kind,
        is_hook=seg.is_hook,
        variant=seg.variant,
        title=seg.title,
        goal_tag=seg.goal_tag,
        image_url=f"/images/{seg.image}" if seg.image else None,
        body=seg.body or {},
    )


def list_chapters(db: Session) -> list[Chapter]:
    return list(db.scalars(select(Chapter).order_by(Chapter.order_no)))


def get_chapter(db: Session, chapter_id: str) -> Chapter | None:
    return db.get(Chapter, chapter_id)


def count_segments(db: Session, chapter_id: str) -> int:
    rows = db.scalars(
        select(Segment).where(Segment.chapter_id == chapter_id, Segment.is_hook == 0)
    )
    return len(list(rows))


def get_segment(db: Session, seg_id: str) -> Segment | None:
    return db.get(Segment, seg_id)


def first_segment(db: Session, chapter_id: str) -> Segment | None:
    return db.scalars(
        select(Segment)
        .where(Segment.chapter_id == chapter_id, Segment.is_hook == 0)
        .order_by(Segment.seq)
        .limit(1)
    ).first()


def cover_image(db: Session, chapter_id: str) -> str | None:
    """章节封面：取第一张有插画的正文页。首页用它当书封。"""
    seg = db.scalars(
        select(Segment)
        .where(
            Segment.chapter_id == chapter_id,
            Segment.is_hook == 0,
            Segment.image.is_not(None),
        )
        .order_by(Segment.seq)
        .limit(1)
    ).first()
    return f"/images/{seg.image}" if seg and seg.image else None


def next_main(db: Session, chapter_id: str, current_seq: int | None) -> Segment | None:
    """主线推进：seq 比当前大的第一段。"""
    if current_seq is None:
        return first_segment(db, chapter_id)
    return db.scalars(
        select(Segment)
        .where(
            Segment.chapter_id == chapter_id,
            Segment.is_hook == 0,
            Segment.seq > current_seq,
        )
        .order_by(Segment.seq)
        .limit(1)
    ).first()


def hooks(db: Session, chapter_id: str) -> dict[str, Segment]:
    rows = db.scalars(
        select(Segment).where(Segment.chapter_id == chapter_id, Segment.is_hook == 1)
    )
    return {s.id: s for s in rows}


def hook_index(db: Session, chapter_id: str) -> list[dict]:
    """按 goal_tag 索引补充牌，供决策规则挑选。

    规则不认识具体片段 id，只按"针对哪个目标"来要牌——这样换章不用改代码。
    """
    rows = db.scalars(
        select(Segment)
        .where(Segment.chapter_id == chapter_id, Segment.is_hook == 1)
        .order_by(Segment.id)
    )
    return [{"id": s.id, "goal": s.goal_tag, "title": s.title} for s in rows]
