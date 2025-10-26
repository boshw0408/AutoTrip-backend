from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    yelp_api_key: str = os.getenv("YELP_API_KEY", "")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    amadeus_api_key: str = os.getenv("AMADEUS_API_KEY", "")
    amadeus_api_secret: str = os.getenv("AMADEUS_API_SECRET", "")
=======
    instagram_access_token: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    instagram_page_id: str = os.getenv("INSTAGRAM_PAGE_ID", "")
    instagram_business_account_id: str = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
>>>>>>> Stashed changes
=======
    instagram_access_token: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    instagram_page_id: str = os.getenv("INSTAGRAM_PAGE_ID", "")
    instagram_business_account_id: str = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
>>>>>>> Stashed changes
    
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
