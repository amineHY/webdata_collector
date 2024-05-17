from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Class to store application settings.
    """

    PROJECT_NAME: str = "Marketplace Crawler"
    ALLOWED_ORIGINS: List[str] = ["http://localhost", "http://localhost:8000"]
    PORT: int = 8000
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    FACEBOOK_EMAIL: str = os.getenv("email")
    FACEBOOK_PASSWORD: str = os.getenv("password")
    HOST: str = os.getenv("HOST", "0.0.0.0")


settings = Settings()
