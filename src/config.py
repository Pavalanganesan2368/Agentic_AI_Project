"""Application configuration loaded from environment variables."""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI E-Commerce Customer Support Agent")
    database_path: Path = ROOT_DIR / os.getenv("DATABASE_PATH", "data/support.db")
    product_index_path: Path = ROOT_DIR / os.getenv("PRODUCT_INDEX_PATH", "data/product_index.json")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")
    llm_provider: str = os.getenv("LLM_PROVIDER", "none")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def ensure_directories(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.product_index_path.parent.mkdir(parents=True, exist_ok=True)

settings = Settings()
