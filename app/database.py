from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


encoded_password = quote_plus(settings.DB_PASSWORD)
# Build Azure SQL connection string
CONNECTION_STRING = (
    f"mssql+pyodbc://{settings.DB_USER}:{encoded_password}"
    f"@{settings.DB_SERVER}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?driver={settings.DB_DRIVER.replace(' ', '+')}"
    f"&Encrypt=yes"
    f"&TrustServerCertificate=no"
    f"&Connection+Timeout=30"
)

# Create engine ← Like PDO connection in Laravel
engine = create_engine(CONNECTION_STRING)



from sqlalchemy import create_engine, URL

connection_url = URL.create(
    drivername="mssql+pyodbc",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,  # ← SQLAlchemy handles encoding automatically
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
    # Connection pooling
    pool_size=5,                    # Keep 5 connections in pool
    max_overflow=10,                # Allow 10 extra connections if needed
    pool_recycle=3600,              # Recycle connections every hour (Azure SQL times out after ~30min)
    pool_pre_ping=True,             # Ping connection before using (validates it's alive)
    echo=False,                     # Set to True for SQL debugging
    # Connection timeout
    connect_args={
        "timeout": 30,
        "TrustServerCertificate": "no",
    }
)

# Session factory ← Like DB::connection() in Laravel
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models ← Like Model extends Eloquent
Base = declarative_base()

# Dependency — gives a DB session per request, closes after
# ← Like Laravel automatically managing DB connections per request
def get_db():
    db = SessionLocal()
    try:
        yield db          # ← Provides DB to the route
    finally:
        db.close()        # ← Always closes connection after request