import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    FASTAUTH_SECRET: str = os.getenv("FASTAUTH_SECRET", "change-me-in-production")


settings = Settings()
