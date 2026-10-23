from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import series

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI Story Forge API – Series, Character Anchors, Stories, Agent Continuator",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(series.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-story-forge"}
