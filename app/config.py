"""Configuration settings for the Voice Summary application."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://username:password@localhost:5432/voicesummary"
    
    # S3 Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    s3_bucket_name: str
    
    # Bolna API Configuration
    bolna_api_key: Optional[str] = None
    
    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
