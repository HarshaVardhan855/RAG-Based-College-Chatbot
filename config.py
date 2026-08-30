import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "College Information Assistant"
    SECRET_KEY: str = "college_rag_secret_key_super_secure_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    ALLOWED_ORIGINS: str = "*"
    DATABASE_URL: str = "sqlite:///./college_rag.db"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    UPLOAD_DIR: str = "./uploads"

    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    LLM_MODEL: str = "gemini-3.6-flash"

    GROK_API_KEY: str = ""
    GROK_MODEL: str = "grok-2-latest"
    GROK_BASE_URL: str = "https://api.x.ai/v1"

    ADMIN_EMAIL: str = "admin@college.edu"
    ADMIN_PASSWORD: str = "Admin@123"

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
