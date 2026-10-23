from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Story Forge API"
    # Safe default for deployments; enable explicitly for local debugging.
    debug: bool = False

    # Browser origins allowed to call the API. Override with a JSON list in .env.
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = False

    # Local upload storage. The API mount and storage service use this same path.
    upload_root: str = "/tmp/ai-story-forge/uploads"

    # Database
    database_url: str = "postgresql+asyncpg://storyforge:storyforge@localhost:5432/storyforge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO / S3
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "storyforge"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
