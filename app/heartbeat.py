import asyncio
import logging
from sqlalchemy import text
from app.database import engine

logger = logging.getLogger(__name__)


async def db_heartbeat():
    """
    Periodically pings the database to keep it alive.
    Prevents Azure SQL free tier from going idle and shutting down.
    """
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            logger.debug("✓ DB heartbeat OK")
        except Exception as e:
            logger.error(f"✗ DB heartbeat failed: {e}")

        # Wait 60 seconds before next ping (your timeout is 2min, so every 1min is safe)
        await asyncio.sleep(60)
