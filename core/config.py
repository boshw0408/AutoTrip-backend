from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    yelp_api_key: str = os.getenv("YELP_API_KEY", "")
    amadeus_api_key: str = os.getenv("AMADEUS_API_KEY", "")
    amadeus_api_secret: str = os.getenv("AMADEUS_API_SECRET", "")
    
    # Cache
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # App Settings
    app_name: str = "Travel AI"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
