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