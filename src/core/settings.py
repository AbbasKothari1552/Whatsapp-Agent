from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

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


settings = Settings()