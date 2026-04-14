from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Production URL Shortener"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/url_shortener"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # App Settings
    BASE_URL: str = "http://localhost:8000"
    
    # Hash configuration
    # Alphabets used for Base62 encoding
    BASE62_ALPHABET: str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
