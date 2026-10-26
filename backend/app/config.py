import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ManiPool Shared Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./manipool.db"
    )

    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "manipool-super-secret-jwt-key-2026-cpi-mahe"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "admin-reviewer-secret-key-cpi")

    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_DOMAINS: List[str] = ["learner.manipal.edu", "manipal.edu"]

    DEV_MODE: bool = os.getenv("DEV_MODE", "true").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
