from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.series import Series
from app.models.character_anchor import CharacterAnchor
from app.schemas.series import SeriesCreate, SeriesUpdate, SeriesOut
from app.schemas.character_anchor import CharacterAnchorCreate, CharacterAnchorUpdate, CharacterAnchorOut

router = APIRouter(prefix="/series", tags=["Series & Character Anchors"])


@router.post("", response_model=SeriesOut, status_code=status.HTTP_201_CREATED)
async def create_series(payload: SeriesCreate, db: AsyncSession = Depends(get_db)):
    series = Series(name=payload.name, description=payload.description)
    db.add(series)
    await db.flush()
    await db.refresh(series)
    return series


@router.get("", response_model=list[SeriesOut])
async def list_series(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Series).order_by(Series.created_at.desc()))
    return result.scalars().all()


@router.get("/{series_id}", response_model=SeriesOut)
async def get_series(series_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Series).where(Series.id == series_id))
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.patch("/{series_id}", response_model=SeriesOut)
async def update_series(series_id: UUID, payload: SeriesUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Series).where(Series.id == series_id))
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    if payload.name is not None:
        series.name = payload.name
    if payload.description is not None:
        series.description = payload.description

    await db.flush()
    await db.refresh(series)
    return series


@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_series(series_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Series).where(Series.id == series_id))
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    await db.delete(series)


# ---------- Character Anchors (vázané na sérii) ----------

@router.post("/{series_id}/characters", response_model=CharacterAnchorOut, status_code=status.HTTP_201_CREATED)
async def create_character(series_id: UUID, payload: CharacterAnchorCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Series).where(Series.id == series_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Series not found")

    character = CharacterAnchor(
        series_id=series_id,
        name=payload.name,
        role=payload.role,
        appearance_text=payload.appearance_text,
        personality=payload.personality,
        backstory=payload.backstory,
        relationships=payload.relationships,
        current_state=payload.current_state,
        consistency_rules=payload.consistency_rules,
        reference_image_ids=payload.reference_image_ids,
    )
    db.add(character)
    try:
        await db.flush()
        await db.refresh(character)
    except Exception as e:
        if "uq_character_name_per_series" in str(e):
            raise HTTPException(status_code=400, detail="Character with this name already exists in the series")
        raise
    return character


@router.get("/{series_id}/characters", response_model=list[CharacterAnchorOut])
async def list_characters(series_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CharacterAnchor)
        .where(CharacterAnchor.series_id == series_id)
        .order_by(CharacterAnchor.name)
    )
    return result.scalars().all()


@router.get("/{series_id}/characters/{character_id}", response_model=CharacterAnchorOut)
async def get_character(series_id: UUID, character_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CharacterAnchor).where(
            CharacterAnchor.id == character_id,
            CharacterAnchor.series_id == series_id,
        )
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found in this series")
    return character


@router.patch("/{series_id}/characters/{character_id}", response_model=CharacterAnchorOut)
async def update_character(
    series_id: UUID,
    character_id: UUID,
    payload: CharacterAnchorUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CharacterAnchor).where(
            CharacterAnchor.id == character_id,
            CharacterAnchor.series_id == series_id,
        )
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found in this series")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)

    await db.flush()
    await db.refresh(character)
    return character


@router.delete("/{series_id}/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(series_id: UUID, character_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CharacterAnchor).where(
            CharacterAnchor.id == character_id,
            CharacterAnchor.series_id == series_id,
        )
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found in this series")
    await db.delete(character)
