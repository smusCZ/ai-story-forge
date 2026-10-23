from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import series, stories

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="AI Story Forge API – Series, Character Anchors, Stories with Genre Profile, Agent Continuator",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(series.router, prefix="/api/v1")
app.include_router(stories.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-story-forge", "version": "0.2.0"}
