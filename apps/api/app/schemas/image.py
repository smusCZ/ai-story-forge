from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ImageFolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    series_id: Optional[UUID] = Field(None, description="Vázané na sérii (doporučeno pro izolaci)")
    story_id: Optional[UUID] = Field(None, description="Vázané na konkrétní příběh")


class ImageFolderOut(BaseModel):
    id: UUID
    name: str
    series_id: Optional[UUID]
    story_id: Optional[UUID]
    created_at: datetime
    image_count: int = 0

    class Config:
        from_attributes = True


class ImageOut(BaseModel):
    id: UUID
    folder_id: UUID
    url: str
    filename: Optional[str]
    tags: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ImageUpdate(BaseModel):
    tags: Optional[list[str]] = None
    filename: Optional[str] = None
