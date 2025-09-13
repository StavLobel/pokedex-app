"""
Application configuration settings
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application settings
    app_name: str = "Pokemon Image Recognition API"
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )
    debug: bool = Field(default=True, description="Enable debug mode")

    # API settings
    api_v1_prefix: str = "/api/v1"
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "*"], description="Trusted hosts"
    )

    # AI Model settings
    model_path: str = Field(
        default="models/pokemon_classifier.pkl", description="Path to AI model file"
    )
    model_type: str = Field(
        default="mock", description="AI model type: mock, pytorch, tensorflow, onnx"
    )
    model_confidence_threshold: float = Field(
        default=0.7, description="Minimum confidence threshold for predictions"
    )
    model_processing_timeout: int = Field(
        default=30, description="Model processing timeout in seconds"
    )

    # Image processing settings
    image_target_size: tuple = Field(
        default=(224, 224), description="Target image size for AI model"
    )
    image_normalize_mean: List[float] = Field(
        default=[0.485, 0.456, 0.406], description="Image normalization mean"
    )
    image_normalize_std: List[float] = Field(
        default=[0.229, 0.224, 0.225], description="Image normalization std"
    )

    # External API settings
    pokeapi_base_url: str = Field(
        default="https://pokeapi.co/api/v2", description="PokéAPI base URL"
    )
    pokeapi_timeout: int = Field(
        default=10, description="PokéAPI request timeout in seconds"
    )

    # File upload settings
    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)"
    )
    allowed_file_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        description="Allowed file MIME types",
    )

    # Database settings (for future use)
    database_url: str = Field(
        default="postgresql://user:password@localhost/pokemon_db",
        description="Database connection URL",
    )

    # Redis settings (for future use)
    redis_url: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="console", description="Log format: json or console"
    )

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
