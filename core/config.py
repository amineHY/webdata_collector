import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Marketplace Crawler"
    ALLOWED_ORIGINS: list = ["http://localhost", "http://localhost:8000"]
    PORT: int = 8000
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    FACEBOOK_EMAIL: str = os.getenv("email")
    FACEBOOK_PASSWORD: str = os.getenv("password")


settings = Settings()
