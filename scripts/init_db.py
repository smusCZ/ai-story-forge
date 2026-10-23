"""
Initialize database schema.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.database import engine, Base
from app.models import *  # noqa: F401,F403


async def main():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done. All tables created.")


if __name__ == "__main__":
    asyncio.run(main())
