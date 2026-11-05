from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    CHAT_MODEL_NAME: str
    temperature: float
    max_retries: int
    GROQ_API_KEY: str

    llm_type: str

    DB_PATH: str

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
