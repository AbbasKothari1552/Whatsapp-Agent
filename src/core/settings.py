from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    GROQ_API_KEY: str

    # Postgres DB settings
    PG_DATABASE_URL: str

    # LLM Models
    QWEN_LLM: str = "qwen/qwen3-32b"
    OPENAI_GPT_120: str = "openai/gpt-oss-120b"
    OPENAI_GPT_20: str = "openai/gpt-oss-20b"
    TEMPERATURE: float = 0.7


settings = Settings()