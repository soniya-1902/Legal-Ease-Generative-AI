from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    app_name: str = "LegalEase"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    backend_url: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    mock_ai: bool = os.getenv("MOCK_AI", "false").lower() in {"1", "true", "yes", "on"}
    allowed_origins: list[str] = [
        item.strip() for item in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501"
        ).split(",") if item.strip()
    ]
    max_document_chars: int = 30000


@lru_cache
def get_settings() -> Settings:
    return Settings()
