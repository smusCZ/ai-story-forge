from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.series import Series
from app.models.story import Story
from app.models.character_anchor import CharacterAnchor
from app.schemas.story import StoryCreate, StoryUpdate, StoryOut
from app.schemas.character_anchor import CharacterAnchorOut

router = APIRouter(prefix="/stories", tags=["Stories"])


@router.post("", response_model=StoryOut, status_code=status.HTTP_201_CREATED)
async def create_story(payload: StoryCreate, db: AsyncSession = Depends(get_db)):
    """
    Vytvoří nový příběh.
    - series_id je povinné (izolace postav)
    - genre (GenreProfile) je povinné – AI z něj vychází od první kapitoly
    """
    result = await db.execute(select(Series).where(Series.id == payload.series_id))
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    story = Story(
        series_id=payload.series_id,
        title=payload.title,
        genre=payload.genre.model_dump(),
        settings=payload.settings,
        status="draft",
    )
    db.add(story)
    await db.flush()
    await db.refresh(story)
    return story


@router.get("", response_model=list[StoryOut])
async def list_stories(
    series_id: UUID | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Story).order_by(Story.created_at.desc())
    if series_id:
        query = query.where(Story.series_id == series_id)
    if status_filter:
        query = query.where(Story.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{story_id}", response_model=StoryOut)
async def get_story(story_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.patch("/{story_id}", response_model=StoryOut)
async def update_story(story_id: UUID, payload: StoryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if payload.title is not None:
        story.title = payload.title
    if payload.status is not None:
        story.status = payload.status
    if payload.genre is not None:
        story.genre = payload.genre.model_dump()
    if payload.settings is not None:
        story.settings = payload.settings

    await db.flush()
    await db.refresh(story)
    return story


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(story_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    await db.delete(story)


@router.get("/{story_id}/characters", response_model=list[CharacterAnchorOut])
async def get_story_characters(story_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Vrátí Character Anchors příběhu = všechny postavy jeho série.
    Toto je klíčové pro konzistenci – generování i agent vždy pracují jen s těmito postavami.
    """
    result = await db.execute(select(Story).where(Story.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    chars_result = await db.execute(
        select(CharacterAnchor)
        .where(CharacterAnchor.series_id == story.series_id)
        .order_by(CharacterAnchor.name)
    )
    return chars_result.scalars().all()
