from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Story Forge API"
    debug: bool = True

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
