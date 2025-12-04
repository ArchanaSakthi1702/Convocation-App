# flush_db.py
import asyncio
from app.database import async_engine  # Your AsyncEngine
from app.models import Base  # Your single models.py containing all tables
from app.auth.security import get_password_hash  # Imported as requested


async def flush_db():
    """
    Drops all tables and recreates them.
    WARNING: This will erase all data in the database!
    """
    async with async_engine.begin() as conn:
        print("⚠️ Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("✅ All tables dropped.")
        print("Creating tables again...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables recreated.")


if __name__ == "__main__":
    confirm = input(
        "Are you sure you want to flush the database? This cannot be undone! (yes/no): "
    )
    if confirm.lower() == "yes":
        asyncio.run(flush_db())
    else:
        print("Operation cancelled.")
