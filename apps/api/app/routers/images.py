from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.image import ImageFolder, Image
from app.models.series import Series
from app.models.story import Story
from app.schemas.image import ImageFolderCreate, ImageFolderOut, ImageOut, ImageUpdate
from app.services.storage import save_upload, delete_file

router = APIRouter(prefix="/images", tags=["Images & Folders"])


@router.post("/folders", response_model=ImageFolderOut, status_code=status.HTTP_201_CREATED)
async def create_folder(payload: ImageFolderCreate, db: AsyncSession = Depends(get_db)):
    if payload.series_id:
        result = await db.execute(select(Series).where(Series.id == payload.series_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Series not found")

    if payload.story_id:
        result = await db.execute(select(Story).where(Story.id == payload.story_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Story not found")

    folder = ImageFolder(
        name=payload.name,
        series_id=payload.series_id,
        story_id=payload.story_id,
    )
    db.add(folder)
    await db.flush()
    await db.refresh(folder)

    return ImageFolderOut(
        id=folder.id,
        name=folder.name,
        series_id=folder.series_id,
        story_id=folder.story_id,
        created_at=folder.created_at,
        image_count=0,
    )


@router.get("/folders", response_model=list[ImageFolderOut])
async def list_folders(
    series_id: UUID | None = None,
    story_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ImageFolder).order_by(ImageFolder.created_at.desc())
    if series_id:
        query = query.where(ImageFolder.series_id == series_id)
    if story_id:
        query = query.where(ImageFolder.story_id == story_id)

    result = await db.execute(query)
    folders = result.scalars().all()

    out = []
    for f in folders:
        count_result = await db.execute(
            select(func.count()).select_from(Image).where(Image.folder_id == f.id)
        )
        count = count_result.scalar() or 0
        out.append(ImageFolderOut(
            id=f.id,
            name=f.name,
            series_id=f.series_id,
            story_id=f.story_id,
            created_at=f.created_at,
            image_count=count,
        ))
    return out


@router.get("/folders/{folder_id}", response_model=ImageFolderOut)
async def get_folder(folder_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ImageFolder).where(ImageFolder.id == folder_id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    count_result = await db.execute(
        select(func.count()).select_from(Image).where(Image.folder_id == folder.id)
    )
    count = count_result.scalar() or 0

    return ImageFolderOut(
        id=folder.id,
        name=folder.name,
        series_id=folder.series_id,
        story_id=folder.story_id,
        created_at=folder.created_at,
        image_count=count,
    )


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(folder_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ImageFolder).where(ImageFolder.id == folder_id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    imgs = await db.execute(select(Image).where(Image.folder_id == folder_id))
    for img in imgs.scalars().all():
        delete_file(img.url)

    await db.delete(folder)


@router.post("/folders/{folder_id}/upload", response_model=list[ImageOut], status_code=status.HTTP_201_CREATED)
async def upload_images(
    folder_id: UUID,
    files: list[UploadFile] = File(...),
    tags: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ImageFolder).where(ImageFolder.id == folder_id))
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Bound the amount of work accepted in a single multipart request.
    if len(files) > 10:
        raise HTTPException(status_code=413, detail="Maximum 10 images per upload request")

    created = []
    saved_urls = []
    try:
        for file in files:
            url, original_name = await save_upload(file, folder_id)
            saved_urls.append(url)

            image = Image(
                folder_id=folder_id,
                url=url,
                filename=original_name,
                tags=tag_list,
            )
            db.add(image)
            await db.flush()
            await db.refresh(image)
            created.append(image)
    except ValueError as e:
        for saved_url in saved_urls:
            delete_file(saved_url)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # The request-scoped DB dependency rolls back on errors; keep filesystem
        # state consistent when any later file or DB operation fails.
        for saved_url in saved_urls:
            delete_file(saved_url)
        raise

    return created


@router.get("/folders/{folder_id}/images", response_model=list[ImageOut])
async def list_images(folder_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ImageFolder).where(ImageFolder.id == folder_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Folder not found")

    imgs = await db.execute(
        select(Image).where(Image.folder_id == folder_id).order_by(Image.created_at.desc())
    )
    return imgs.scalars().all()


@router.patch("/{image_id}", response_model=ImageOut)
async def update_image(image_id: UUID, payload: ImageUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if payload.tags is not None:
        image.tags = payload.tags
    if payload.filename is not None:
        image.filename = payload.filename

    await db.flush()
    await db.refresh(image)
    return image


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    delete_file(image.url)
    await db.delete(image)


@router.get("/inspiration")
async def get_inspiration(
    series_id: UUID | None = None,
    story_id: UUID | None = None,
    query: str | None = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Vrátí inspirativní obrázky pro generování.
    Filtruje podle series_id / story_id (izolace).
    query: jednoduché fulltext (MVP) – později CLIP + pgvector.
    """
    from sqlalchemy import or_

    q = select(Image).join(ImageFolder)

    if series_id:
        q = q.where(ImageFolder.series_id == series_id)
    if story_id:
        q = q.where(ImageFolder.story_id == story_id)

    if query:
        q = q.where(
            or_(
                Image.filename.ilike(f"%{query}%"),
                Image.tags.any(query),
            )
        )

    q = q.order_by(Image.created_at.desc()).limit(min(limit, 50))
    result = await db.execute(q)
    return result.scalars().all()
