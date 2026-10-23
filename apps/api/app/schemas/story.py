from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Any


class GenreProfile(BaseModel):
    """Povinný žánrový profil příběhu – AI z něj vychází při generování i pokračováních."""
    main: str = Field(..., min_length=1, description="Hlavní žánr (např. anime isekai, dark fantasy, hard sci-fi)")
    secondary: list[str] = Field(default_factory=list, description="Sekundární žánry / subžánry")
    tone: str = Field(..., min_length=1, description="Tón (dark, light, melancholický, humoristický, epický...)")
    tempo: str = Field(default="medium", description="Tempo vyprávění (slow, medium, fast)")
    style: str = Field(default="third_person", description="Styl vyprávění (first_person, third_person, script...)")
    target_chapter_length: str = Field(default="medium", description="Cílová délka kapitol (short, medium, long)")
    notes: Optional[str] = Field(None, description="Další poznámky pro AI")


class StoryCreate(BaseModel):
    series_id: UUID = Field(..., description="Povinné – příběh patří do konkrétní série")
    title: str = Field(..., min_length=1, max_length=500)
    genre: GenreProfile
    settings: dict[str, Any] = Field(default_factory=dict)


class StoryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|completed)$")
    genre: Optional[GenreProfile] = None
    settings: Optional[dict[str, Any]] = None


class StoryOut(BaseModel):
    id: UUID
    series_id: UUID
    title: str
    status: str
    genre: dict[str, Any]
    settings: dict[str, Any]
    engagement_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
