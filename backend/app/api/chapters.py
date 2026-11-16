"""章节接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ChapterOut
from ..services import content

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


def _out(db: Session, c) -> ChapterOut:
    return ChapterOut(
        id=c.id,
        title=c.title,
        subtitle=c.subtitle,
        topic=c.topic,
        order_no=c.order_no,
        segment_count=content.count_segments(db, c.id),
        cover_url=content.cover_image(db, c.id),
    )


@router.get("", response_model=list[ChapterOut])
def list_chapters(db: Session = Depends(get_db)):
    return [_out(db, c) for c in content.list_chapters(db)]


@router.get("/{chapter_id}", response_model=ChapterOut)
def get_chapter(chapter_id: str, db: Session = Depends(get_db)):
    c = content.get_chapter(db, chapter_id)
    if c is None:
        raise HTTPException(status_code=404, detail="chapter not found")
    return _out(db, c)
