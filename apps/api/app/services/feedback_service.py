"""
Feedback & Engagement service.
Simple, free, no external paid sentiment API needed for MVP.
Later can be upgraded with free local models.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.feedback import Feedback
from app.models.chapter import Chapter
from app.models.story import Story
from app.schemas.feedback import FeedbackSummary


POSITIVE_WORDS = {"skvělé", "super", "líbí", "amazing", "love", "great", "good", "yes", "ano", "perfektní", "krásné", "epic"}
NEGATIVE_WORDS = {"nudné", "špatné", "hate", "boring", "bad", "no", "ne", "horší", "nesmysl", "weak"}


def simple_sentiment(text: str | None) -> float:
    if not text:
        return 0.0
    t = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos == 0 and neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg)


async def compute_chapter_summary(db: AsyncSession, chapter_id: UUID) -> FeedbackSummary:
    result = await db.execute(select(Feedback).where(Feedback.chapter_id == chapter_id))
    items = result.scalars().all()

    likes = sum(1 for f in items if f.type == "like")
    dislikes = sum(1 for f in items if f.type == "dislike")
    comments = [f for f in items if f.type == "comment"]
    emojis = sum(1 for f in items if f.type == "emoji")
    times = [float(f.content) for f in items if f.type == "time_spent" and f.content and f.content.replace(".", "").isdigit()]

    avg_time = sum(times) / len(times) if times else None

    total_reactions = likes + dislikes + len(comments) + emojis
    if total_reactions == 0:
        score = 0.0
    else:
        like_ratio = likes / max(likes + dislikes, 1)
        comment_bonus = min(len(comments) * 0.05, 0.3)
        time_bonus = min((avg_time or 0) / 300, 0.2)
        score = round(min(1.0, like_ratio * 0.5 + comment_bonus + time_bonus + (likes * 0.05)), 3)

    recent = [f.content for f in comments if f.content][-5:]

    return FeedbackSummary(
        chapter_id=chapter_id,
        likes=likes,
        dislikes=dislikes,
        comments=len(comments),
        emojis=emojis,
        avg_time_spent=avg_time,
        engagement_score=score,
        recent_comments=recent,
    )


async def update_story_engagement(db: AsyncSession, story_id: UUID) -> float:
    chapters = (await db.execute(select(Chapter.id).where(Chapter.story_id == story_id))).scalars().all()
    if not chapters:
        return 0.0

    scores = []
    for ch_id in chapters:
        summary = await compute_chapter_summary(db, ch_id)
        scores.append(summary.engagement_score)

    avg = round(sum(scores) / len(scores), 3) if scores else 0.0

    story = (await db.execute(select(Story).where(Story.id == story_id))).scalar_one_or_none()
    if story:
        story.engagement_score = avg
        await db.flush()

    return avg
