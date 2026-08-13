import asyncio
import logging
from sqlalchemy import text
from app.core.config import settings
from app.database import engine

logger = logging.getLogger(__name__)


async def db_heartbeat():
    """
    Periodically pings the database to keep the connection alive.
    Primarily needed for MSSQL (Azure SQL free tier goes idle after ~2 min).
    PostgreSQL managed services (e.g. Aiven) do not need this.
    """
    logger.info(f"DB heartbeat started (dialect: {settings.DB_CONNECTIVITY})")

    while True:
        try:
            if settings.DB_CONNECTIVITY == "MSSQL":
                # Sync engine — use regular connect()
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    conn.commit()
            elif settings.DB_CONNECTIVITY == "POSTGRESQL":
                # Async engine — must use async context manager
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))

            logger.debug("✓ DB heartbeat OK")

        except Exception as e:
            logger.error(f"✗ DB heartbeat failed: {e}")

        # Ping every 60 seconds (safe margin for a 2-min idle timeout)
        await asyncio.sleep(60)

