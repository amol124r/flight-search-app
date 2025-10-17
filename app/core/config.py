from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Amadeus API
    amadeus_api_key: str = os.getenv("AMADEUS_API_KEY", "")
    amadeus_api_secret: str = os.getenv("AMADEUS_API_SECRET", "")
    amadeus_environment: str = os.getenv("AMADEUS_ENVIRONMENT", "test")
    
    # App Configuration
    app_name: str = "Flight Search App"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8030"))
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    allowed_origins: List[str] = [
        "http://localhost:3001",
        "http://localhost:8030",
        "http://127.0.0.1:8030"
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()
