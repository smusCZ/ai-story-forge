from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.story import Story
from app.models.agent_run import AgentRun
from app.schemas.agent import AgentTriggerRequest, AgentRunOut, AgentRunHistoryItem
from app.services.agent_continuator import run_agent, _load_context, _decide

router = APIRouter(prefix="/agent", tags=["Agent Continuator"])


@router.post("/trigger/{story_id}", response_model=AgentRunOut)
async def trigger_agent(
    story_id: UUID,
    payload: AgentTriggerRequest = AgentTriggerRequest(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Story).where(Story.id == story_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    try:
        outcome = await run_agent(db, story_id, force_action=payload.force_action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")

    return outcome


@router.get("/runs/{story_id}", response_model=list[AgentRunHistoryItem])
async def list_agent_runs(story_id: UUID, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.story_id == story_id)
        .order_by(AgentRun.created_at.desc())
        .limit(min(limit, 50))
    )
    return result.scalars().all()


@router.get("/recommend/{story_id}")
async def recommend_action(story_id: UUID, db: AsyncSession = Depends(get_db)):
    """Pouze doporučí další akci bez generování."""
    result = await db.execute(select(Story).where(Story.id == story_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    context = await _load_context(db, story_id)
    decision, reasoning = await _decide(context)

    return {
        "story_id": str(story_id),
        "recommended_action": decision,
        "reasoning": reasoning,
        "engagement_score": context["engagement_score"],
        "has_chapters": context["latest_chapter"] is not None,
    }
