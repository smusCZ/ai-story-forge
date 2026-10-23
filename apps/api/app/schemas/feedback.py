from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal


class FeedbackCreate(BaseModel):
    type: Literal["like", "dislike", "comment", "emoji", "time_spent"] = Field(..., description="Typ reakce")
    content: Optional[str] = Field(None, description="Text komentáře, emoji, nebo počet sekund u time_spent")
    user_id: Optional[UUID] = None


class FeedbackOut(BaseModel):
    id: UUID
    chapter_id: UUID
    user_id: Optional[UUID]
    type: str
    content: Optional[str]
    sentiment_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackSummary(BaseModel):
    chapter_id: UUID
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    emojis: int = 0
    avg_time_spent: Optional[float] = None
    engagement_score: float = 0.0
    recent_comments: list[str] = []
