from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.chapter import Chapter
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackOut, FeedbackSummary
from app.services.feedback_service import simple_sentiment, compute_chapter_summary, update_story_engagement

router = APIRouter(tags=["Feedback"])


@router.post("/chapters/{chapter_id}/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    chapter_id: UUID,
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    sentiment = None
    if payload.type == "comment":
        sentiment = simple_sentiment(payload.content)
    elif payload.type == "like":
        sentiment = 1.0
    elif payload.type == "dislike":
        sentiment = -1.0

    fb = Feedback(
        chapter_id=chapter_id,
        user_id=payload.user_id,
        type=payload.type,
        content=payload.content,
        sentiment_score=sentiment,
    )
    db.add(fb)
    await db.flush()
    await db.refresh(fb)

    await update_story_engagement(db, chapter.story_id)
    return fb


@router.get("/chapters/{chapter_id}/feedback", response_model=list[FeedbackOut])
async def list_feedback(chapter_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Feedback)
        .where(Feedback.chapter_id == chapter_id)
        .order_by(Feedback.created_at.desc())
    )
    return result.scalars().all()


@router.get("/chapters/{chapter_id}/feedback/summary", response_model=FeedbackSummary)
async def feedback_summary(chapter_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chapter not found")
    return await compute_chapter_summary(db, chapter_id)


@router.get("/stories/{story_id}/engagement")
async def story_engagement(story_id: UUID, db: AsyncSession = Depends(get_db)):
    from app.models.story import Story
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    score = await update_story_engagement(db, story_id)
    return {"story_id": story_id, "engagement_score": score}
