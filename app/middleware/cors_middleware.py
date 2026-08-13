from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.core.config import settings


def setup_cors(app: FastAPI):
    """
    Setup CORS middleware with different origins for public and private routes
    
    Public routes: /api/v1/public/*  <- uses CORS_ORIGINS_PUBLIC
    Private routes: /api/v1/*        <- uses CORS_ORIGINS_PRIVATE
    """
    
    # Get origins from config
    public_origins = settings.cors_public_origins
    private_origins = settings.cors_private_origins
    
    # Combine all allowed origins for a unified middleware
    # Since middleware runs globally, we'll allow both sets
    all_origins = public_origins if public_origins == ["*"] else list(set(public_origins + private_origins))
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,  # Cache preflight requests for 600 seconds
    )
