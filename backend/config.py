"""
Configuration management for HexaNote backend.
Uses Pydantic settings for environment variable management.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables or defaults."""

    # Application
    app_name: str = "HexaNote"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/hexanote.db"

    # Weaviate
    weaviate_url: str = "http://weaviate:8080"
    weaviate_api_key: str = "user-a-key"
    weaviate_timeout_init: int = 60
    weaviate_timeout_query: int = 1800  # 30 minutes for slow CPU inference
    weaviate_timeout_insert: int = 300

    # Ollama
    ollama_url: str = "http://ollama:11434"
    ollama_embedding_model: str = "mxbai-embed-large:latest"
    ollama_generation_model: str = "llama3.2:1b"

    # Authentication (simple single-user auth)
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    simple_password: str = "hexanote"  # Simple password for single-user

    # CORS
    cors_origins: list[str] = ["*"]  # Allow all origins for local network

    # Sync
    websocket_heartbeat_interval: int = 30  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
