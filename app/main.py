import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.routers.v1.api import api
from app.routers.v1.public_api import public_api
from app.heartbeat import db_heartbeat
from app.middleware.cors_middleware import setup_cors

heartbeat_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown"""
    global heartbeat_task
    # Startup
    if(settings.DB_CONNECTIVITY == "MSSQL"):
     heartbeat_task = asyncio.create_task(db_heartbeat())
    yield
    # Shutdown
    if heartbeat_task:
        heartbeat_task.cancel()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.APP_DEBUG,
    lifespan=lifespan
)

# Setup CORS for public and private routes
setup_cors(app)

app.include_router(api, prefix="/api/v1")
app.include_router(public_api, prefix="/api/v1/public")