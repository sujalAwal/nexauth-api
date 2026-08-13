from sqlalchemy import create_engine, URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from urllib.parse import quote_plus

# ── Single declarative Base for ALL models ───────────────────────────────────
# IMPORTANT: Must be declared ONCE at module level, outside any conditional.
# Every model in every module imports this Base. If it were declared inside
# an if/elif block, models imported before that block runs would attach to
# a different (or missing) Base, causing silent metadata mismatches.
class Base(DeclarativeBase):
    pass


# ── Database engine + session factory — chosen by DB_CONNECTIVITY env var ────

if settings.DB_CONNECTIVITY == "MSSQL":
    # Synchronous engine for Azure SQL / MSSQL
    connection_url = URL.create(
        drivername="mssql+pyodbc",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_SERVER,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        query={
            "driver": settings.DB_DRIVER,
            "Encrypt": "yes",
            "TrustServerCertificate": "no",
            "Connection Timeout": "30",
        }
    )

    engine = create_engine(
        connection_url,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,          # Azure SQL free tier idles after ~30 min
        pool_pre_ping=True,
        echo=settings.APP_DEBUG,
        connect_args={
            "timeout": 30,
            "TrustServerCertificate": "no",
        }
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

elif settings.DB_CONNECTIVITY == "POSTGRESQL":
    # Async engine for PostgreSQL via asyncpg
    DATABASE_URL = (
    f"postgresql+asyncpg://{quote_plus(settings.DB_USER)}:{quote_plus(settings.DB_PASSWORD)}"
    f"@{settings.DB_SERVER}:{settings.DB_PORT}/{settings.DB_NAME}"
    )

    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.APP_DEBUG,    # only log SQL in debug mode
        pool_size=10,               # base pool — handles concurrent async requests
        max_overflow=20,            # extra connections allowed under spike load
        pool_timeout=30,            # seconds to wait for a free connection
        pool_recycle=1800,          # recycle connections every 30 min
        pool_pre_ping=True,         # validate connection health before use
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,     # prevent lazy-load errors after commit in async
    )

    async def get_db():
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

else:
    raise ValueError(
        f"Unsupported DB_CONNECTIVITY value: '{settings.DB_CONNECTIVITY}'. "
        "Expected 'MSSQL' or 'POSTGRESQL'."
    )