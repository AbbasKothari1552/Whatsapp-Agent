from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client.http.models import Distance

from src.core.embeddings import (
    _embed_text,
    _embed_image,
)

from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    # temp data directory
    DATA_DIR: str = "data"

    GROQ_API_KEY: str

    # Postgres DB settings
    PG_DATABASE_URL: str
    PG_DATABASE_URL_CLIENT: str
    CLIENT_SCHEMA_NAME: str = "dbo"
    MSSQL_DATABASE_DSN: str

    # QDrant Vector DB settings
    QDRANT_URL: str
    QDRANT_API_KEY: str = ""
    COLLECTION_NAME: str = "whatsapp_agent"
    EMBEDDING_DIM: int = 384

    COLLECTIONS_CONFIG: dict = {
        "whatsapp_agent": {
                "dim": 384,  # e.g. settings.EMBEDDING_DIM
                "distance": Distance.COSINE,
                "embed_fn": _embed_text
            },
        "image_products": {
            "dim": 512,  # depends on your image encoder
            "distance": Distance.COSINE,
            "embed_fn": _embed_image
        }
    }

    # LLM Models
    QWEN_LLM: str = "qwen/qwen3-32b"
    OPENAI_GPT_120: str = "openai/gpt-oss-120b"
    OPENAI_GPT_20: str = "openai/gpt-oss-20b"
    TEMPERATURE: float = 0.7
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # logging settings
    DEBUG: bool = False
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: Path  = Path("logs")

    # Langsmith settings
    LANGSMITH_API_KEY: str
    LANGSMITH_TRACING: str 
    LANGSMITH_ENDPOINT: str 
    LANGSMITH_PROJECT: str 

    # Audio Transcription settings
    AUDIO_EXTENSIONS: list = ["mp3", "wav", "ogg", "opus"]
    AUDIO_MODEL: str = "whisper-large-v3"

    # Easyocr Languages list
    EASYOCR_LANGUAGES: list = ['en']


settings = Settings()