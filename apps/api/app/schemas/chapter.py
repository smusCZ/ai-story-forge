from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ChapterGenerateRequest(BaseModel):
    instruction: Optional[str] = Field(None, description="Volitelná instrukce pro generování")
    use_inspiration: bool = Field(True, description="Použít inspiraci z nahraných obrázků")


class ChapterOut(BaseModel):
    id: UUID
    story_id: UUID
    chapter_number: int
    title: Optional[str]
    content: str
    summary: Optional[str]
    status: str
    generated_by: str
    parent_chapter_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|rewritten)$")
