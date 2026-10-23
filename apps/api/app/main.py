from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routers import series, stories, images, chapters, feedback, agent

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.6.0",
    description="AI Story Forge API – Full pipeline including Agent Continuator",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = Path(settings.upload_root).expanduser()
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(series.router, prefix="/api/v1")
app.include_router(stories.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")
app.include_router(chapters.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-story-forge", "version": "0.6.0"}
