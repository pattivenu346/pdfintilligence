from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./question_papers.db"
    storage_path: Path = Path("./storage")
    max_upload_mb: int = 500

    class Config:
        env_file = ".env"


settings = Settings()
settings.storage_path.mkdir(parents=True, exist_ok=True)
