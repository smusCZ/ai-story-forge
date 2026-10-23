from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.story import Story
from app.models.chapter import Chapter
from app.schemas.chapter import ChapterGenerateRequest, ChapterOut, ChapterUpdate
from app.services.story_generator import generate_chapter

router = APIRouter(prefix="/stories/{story_id}/chapters", tags=["Chapters & Generation"])


@router.post("/generate", response_model=ChapterOut, status_code=status.HTTP_201_CREATED)
async def generate_next_chapter(
    story_id: UUID,
    payload: ChapterGenerateRequest = ChapterGenerateRequest(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Story).where(Story.id == story_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Story not found")

    try:
        chapter = await generate_chapter(
            db=db,
            story_id=story_id,
            user_instruction=payload.instruction,
            use_inspiration=payload.use_inspiration,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    return chapter


@router.get("", response_model=list[ChapterOut])
async def list_chapters(story_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter)
        .where(Chapter.story_id == story_id)
        .order_by(Chapter.chapter_number)
    )
    return result.scalars().all()


@router.get("/{chapter_id}", response_model=ChapterOut)
async def get_chapter(story_id: UUID, chapter_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.story_id == story_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.patch("/{chapter_id}", response_model=ChapterOut)
async def update_chapter(
    story_id: UUID,
    chapter_id: UUID,
    payload: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.story_id == story_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(chapter, k, v)

    await db.flush()
    await db.refresh(chapter)
    return chapter
