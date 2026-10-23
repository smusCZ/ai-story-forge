from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Any


class CharacterAnchorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: Optional[str] = None
    appearance_text: Optional[str] = None
    personality: dict[str, Any] = Field(default_factory=dict)
    backstory: Optional[str] = None
    relationships: dict[str, Any] = Field(default_factory=dict)
    current_state: Optional[str] = None
    consistency_rules: dict[str, Any] = Field(default_factory=dict)
    reference_image_ids: list[UUID] = Field(default_factory=list)


class CharacterAnchorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = None
    appearance_text: Optional[str] = None
    personality: Optional[dict[str, Any]] = None
    backstory: Optional[str] = None
    relationships: Optional[dict[str, Any]] = None
    current_state: Optional[str] = None
    consistency_rules: Optional[dict[str, Any]] = None
    reference_image_ids: Optional[list[UUID]] = None


class CharacterAnchorOut(BaseModel):
    id: UUID
    series_id: UUID
    name: str
    role: Optional[str]
    appearance_text: Optional[str]
    personality: dict[str, Any]
    backstory: Optional[str]
    relationships: dict[str, Any]
    current_state: Optional[str]
    consistency_rules: dict[str, Any]
    reference_image_ids: list[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
