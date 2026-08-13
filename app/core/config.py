from pydantic import  EmailStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "NexAuth"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_URL: str = "http://localhost:8000"

    # Database
    DB_CONNECTIVITY: str = "MSSQL"
    DB_DRIVER: str
    DB_SERVER: str
    DB_PORT: int = 1433
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    REDIS_HOST: str
    REDIS_PASSWORD: str
    REDIS_DB  : int = 0
    REDIS_PORT: int = 6379

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 22

    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_FROM_NAME: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_TLS: bool 
    MAIL_SSL: bool 
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # CORS
    CORS_ORIGINS_PUBLIC: str = "*"  # comma-separated: domain1.com,domain2.com
    CORS_ORIGINS_PRIVATE: str = "http://localhost:3000"  # comma-separated

    # Chatbot
    DOCUMENTS_PATH: str = "documents"
    MAX_CHUNKS_PER_QUERY: int = 5
    SIMILARITY_THRESHOLD: float = 0.5
    FALLBACK_SIMILARITY_THRESHOLD: float = 0.2
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    EMBEDDING_TOKENS_LIMIT: int = 8191
    MAX_CONTEXT_TOKENS: int = 8192
    CONTEXT_RESERVE_TOKENS: int = 1024
    CONTEXT_HISTORY_MESSAGES: int = 10

    # Sync file-size window (MB). Files outside [min, max] are kept in the
    # sharepoints catalog but excluded from embedding/sync.
    SYNC_MIN_FILE_SIZE_MB: float = 0
    SYNC_MAX_FILE_SIZE_MB: float = 100.0
    # Sync runs at most this many files per batch before persisting.
    SYNC_BATCH_SIZE: int = 50

    @property
    def sync_min_file_size_bytes(self) -> int:
        return int(self.SYNC_MIN_FILE_SIZE_MB * 1024 * 1024)

    @property
    def sync_max_file_size_bytes(self) -> int:
        return int(self.SYNC_MAX_FILE_SIZE_MB * 1024 * 1024)

    # LLM providers
    PRIMARY_LLM: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_BASE_URL: str = ""
    AZURE_OPENAI_MODEL: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-06-01"
    ANTHROPIC_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_VERSION: str = "2024-06-01"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_BATCH_SIZE: int = 64

    # Azure SharePoint
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    AZURE_TENANT_ID: str = ""

    class Config:
        env_file = ".env"
    
    @property
    def cors_public_origins(self) -> list:
        """Parse comma-separated public origins"""
        if self.CORS_ORIGINS_PUBLIC == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS_PUBLIC.split(",")]
    
    @property
    def cors_private_origins(self) -> list:
        """Parse comma-separated private origins"""
        return [origin.strip() for origin in self.CORS_ORIGINS_PRIVATE.split(",")]

settings = Settings()