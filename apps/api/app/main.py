from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.routers import series, stories, images

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="AI Story Forge API – Series, Character Anchors, Stories, Image Inspiration, Agent Continuator",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = Path("/tmp/ai-story-forge/uploads")
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(series.router, prefix="/api/v1")
app.include_router(stories.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-story-forge", "version": "0.3.0"}
