import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings and configuration"""

    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "emo_now")

    # API settings
    API_TITLE: str = "I'm Emo Now API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Emotion tracking application backend API"

    # File upload settings
    MAX_VIDEO_SIZE: int = int(os.getenv("MAX_VIDEO_SIZE", 100 * 1024 * 1024))  # 100MB default
    ALLOWED_VIDEO_TYPES: list[str] = ["video/mp4", "video/quicktime", "video/x-msvideo"]

    # CORS settings
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # Data retention (days)
    DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", 90))

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    @property
    def mongodb_client_kwargs(self) -> dict:
        """Return MongoDB client connection kwargs"""
        return {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 10000,
        }


settings = Settings()
