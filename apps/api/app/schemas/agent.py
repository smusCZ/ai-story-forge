from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Any, Literal


class AgentTriggerRequest(BaseModel):
    force_action: Optional[Literal["continue", "rewrite", "branch", "new_arc", "review"]] = Field(
        None, description="Volitelně vynutit konkrétní akci místo automatického rozhodnutí"
    )


class AgentRunOut(BaseModel):
    run_id: str
    story_id: str
    action: str
    reasoning: str
    result: dict[str, Any]


class AgentRunHistoryItem(BaseModel):
    id: UUID
    story_id: UUID
    action_taken: Optional[str]
    reasoning: Optional[str]
    output: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True
