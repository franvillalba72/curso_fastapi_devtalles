import os


class Settings:
    """Application settings."""

    JWT_SECRET_KEY: str = os.getenv("SECRET_KEY", "your_default_secret_key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
